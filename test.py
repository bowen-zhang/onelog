import geopy
import io
import logging

from common import pattern
from common import unit
from flightdata import io as flightdata_io
from flightdata import definitions
from onelog.core import engine
from onelog.core import essential
from onelog.core import models


class FlightDataAnalyzer(pattern.Logger):

  def __init__(self, *args, **kwargs):
    super(FlightDataAnalyzer, self).__init__(*args, **kwargs)

  def analyze(self):
    flight_data = models.FlightData.objects.order_by('-last_update').first()
    if flight_data == None:
      self.logger.info('No flight data to analyze.')
      return

    self.logger.info('Analyzing flight {0}...'.format(flight_data.flight_id))

    stream = io.BytesIO(flight_data.data)
    reader = flightdata_io.CompressedFlightDataReader(stream)
    log_entry = models.LogEntry()
    processors = [
        FlightDataAggregator(),
        NearbyAirportMarker(),
        StopMarker(),
        DepartureAirportDetector(log_entry),
        ArrivalAirportDetector(log_entry),
        RouteDetector(log_entry),
        LandingsDetector(log_entry),
        InOutTimeDetector(log_entry),
        Dump(),
    ]
    prev = reader
    for processor in processors:
      prev.on('data', processor.on_data)
      prev = processor
    reader.read()
    for processor in processors:
      processor.done()

    compute_engine = engine.ComputeEngine()
    compute_engine.compute(log_entry)
    print log_entry.dump()

  def _on_data(self, timestamp, datum):
    for data_type in datum:
      value = datum[data_type]
      self.logger.debug('{0}: {1}={2}'.format(timestamp, data_type.name,
                                              data_type.normalize(value)))


class DataProcessor(object):

  def done(self):
    pass


class FlightDataAggregator(DataProcessor, pattern.EventEmitter):

  def __init__(self, *args, **kwargs):
    super(FlightDataAggregator, self).__init__(*args, **kwargs)
    self._datum = {}

  def on_data(self, timestamp, datum):
    for data_type in datum:
      self._datum[data_type] = datum[data_type]
    self.emit('data', timestamp, dict(self._datum))


class NearbyAirportMarker(DataProcessor, pattern.EventEmitter):

  _DISTANCE_THRESHOLD = unit.Length(2, unit.Length.STATUTE_MILE)
  _MILE_TO_DEGREE = 1 / 3963.2

  def __init__(self, *args, **kwargs):
    super(NearbyAirportMarker, self).__init__(*args, **kwargs)
    self._last_position = None
    self._last_airport = None

  def on_data(self, timestamp, datum):
    if definitions.DataType.LATITUDE not in datum or definitions.DataType.LONGITUDE not in datum:
      self.emit('data', timestamp, datum)
      return

    lon = datum[definitions.DataType.LONGITUDE]
    lat = datum[definitions.DataType.LATITUDE]

    if self._last_position:
      distance = geopy.distance.great_circle(self._last_position, (lat, lon))
      if distance.miles < 1:
        if self._last_airport:
          datum['nearby_airport'] = self._last_airport
        self.emit('data', timestamp, datum)
        return

    self._last_airport = models.Airport.objects(
        location__near=[lon.degree, lat.degree],
        location__max_distance=NearbyAirportMarker._DISTANCE_THRESHOLD.sm /
        NearbyAirportMarker._MILE_TO_DEGREE).first()

    if self._last_airport:
      datum['nearby_airport'] = self._last_airport
    self.emit('data', timestamp, datum)


class StopMarker(DataProcessor, pattern.EventEmitter):

  _ALTITUDE_THRESHOLD = unit.Length(25, unit.Length.FOOT)

  def __init__(self, *args, **kwargs):
    super(StopMarker, self).__init__(*args, **kwargs)

  def on_data(self, timestamp, datum):
    if definitions.DataType.GROUND_SPEED not in datum or definitions.DataType.ALTITUDE not in datum or 'nearby_airport' not in datum:
      self.emit('data', timestamp, datum)
      return

    alt = datum[definitions.DataType.ALTITUDE]
    airport = datum['nearby_airport']
    agl = alt.ft - airport.elevation
    if agl < StopMarker._ALTITUDE_THRESHOLD.ft:
      datum['airport'] = airport

    self.emit('data', timestamp, datum)


class DepartureAirportDetector(DataProcessor, pattern.EventEmitter):

  def __init__(self, log_entry, *args, **kwargs):
    super(DepartureAirportDetector, self).__init__(*args, **kwargs)
    self._log_entry = log_entry
    self._airport = None

  def on_data(self, timestamp, datum):
    if 'airport' in datum and not self._airport:
      self._airport = datum['airport']
      self._log_entry.add_field(essential.DepartureAirport,
                                self._airport.icao_id)
    self.emit('data', timestamp, datum)


class ArrivalAirportDetector(DataProcessor, pattern.EventEmitter):

  def __init__(self, log_entry, *args, **kwargs):
    super(ArrivalAirportDetector, self).__init__(*args, **kwargs)
    self._log_entry = log_entry
    self._airport = None

  def on_data(self, timestamp, datum):
    if 'airport' in datum:
      self._airport = datum['airport']
    self.emit('data', timestamp, datum)

  def done(self):
    if self._airport:
      self._log_entry.add_field(essential.ArrivalAirport,
                                self._airport.icao_id)


class RouteDetector(DataProcessor, pattern.EventEmitter):

  def __init__(self, log_entry, *args, **kwargs):
    super(RouteDetector, self).__init__(*args, **kwargs)
    self._log_entry = log_entry
    self._routes = []
    self._last_airport = None

  def on_data(self, timestamp, datum):
    if 'nearby_airport' in datum:
      airport = datum['nearby_airport']
      if not self._last_airport or self._last_airport.icao_id != airport.icao_id:
        self._last_airport = airport
        self._routes.append(airport.icao_id)

    self.emit('data', timestamp, datum)

  def done(self):
    if len(self._routes) > 2:
      route = ' '.join(self._routes[1:-1])
      self._log_entry.add_field(essential.Route, route)


class LandingsDetector(DataProcessor, pattern.EventEmitter):

  def __init__(self, log_entry, *args, **kwargs):
    super(LandingsDetector, self).__init__(*args, **kwargs)
    self._log_entry = log_entry
    self._landings = 0
    self._flying = None

  def on_data(self, timestamp, datum):
    if 'airport' in datum:
      if self._flying:
        print 'Landed at {0}'.format(datum['airport'].icao_id)
        self._landings += 1
      self._flying = False
    else:
      if self._flying == False:
        self._flying = True

    self.emit('data', timestamp, datum)

  def done(self):
    self._log_entry.add_field(essential.DayLanding, self._landings)


class InOutTimeDetector(DataProcessor, pattern.EventEmitter):

  def __init__(self, log_entry, *args, **kwargs):
    super(InOutTimeDetector, self).__init__(*args, **kwargs)
    self._log_entry = log_entry
    self._start_time = None
    self._end_time = None

  def on_data(self, timestamp, datum):
    if not self._start_time:
      self._start_time = timestamp
    self._end_time = timestamp

    self.emit('data', timestamp, datum)

  def done(self):
    if self._start_time:
      self._log_entry.add_field(essential.TimeOut, self._start_time)
    if self._end_time:
      self._log_entry.add_field(essential.TimeIn, self._end_time)


class Dump(DataProcessor, pattern.Logger):

  def __init__(self, *args, **kwargs):
    super(Dump, self).__init__(*args, **kwargs)
    self._file = open('dump.txt', 'w')

  def on_data(self, timestamp, datum):
    speed = datum[
        definitions.DataType.
        GROUND_SPEED].knots if definitions.DataType.GROUND_SPEED in datum else '-'
    alt = datum[definitions.DataType.
                ALTITUDE].ft if definitions.DataType.ALTITUDE in datum else '-'
    nearby_airport = datum[
        'nearby_airport'].icao_id if 'nearby_airport' in datum else '-'
    airport = datum['airport'].icao_id if 'airport' in datum else '-'
    self._file.write('{0}\t{1}\t{2}\t{3}\t{4}\n'.format(
        timestamp, speed, alt, nearby_airport, airport))

  def done(self):
    self._file.close()


def main():
  FlightDataAnalyzer().analyze()


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  main()

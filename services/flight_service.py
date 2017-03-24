import datetime

from flightdata import flight_pb2
from flightdata import flight_pb2_grpc
from onelog.core import analyzer
from onelog.core import essential
from onelog.core import models
from common import pattern


class FlightService(flight_pb2_grpc.FlightServiceServicer, pattern.Logger):

  def Notify(self, flight_event, context):
    self.logger.info('Notify flight event...(id={0}, event={1})'.format(
        flight_event.flight_id, flight_event.event_type))

    entry = models.FlightEvent()
    entry.flight_id = flight_event.flight_id
    entry.event_type = flight_event.event_type
    entry.timestamp = flight_event.timestamp
    entry.save()

    return flight_pb2.Receipt(succeed=True)

  def UploadFlightData(self, flight_data, context):
    self.logger.info(
        'Uploading flight data...(id={0}, index={1}, final={2})'.format(
            flight_data.id, flight_data.index, flight_data.final))

    entry = None
    if flight_data.index == 0:
      if models.FlightData.objects(flight_id=flight_data.id).count() > 0:
        return flight_pb2.Receipt(
            succeed=False, message='Flight id already exist.')

      entry = models.FlightData()
      entry.flight_id = flight_data.id
      entry.data = flight_data.data
    else:
      entry = models.FlightData.objects(flight_id=flight_data.id).first()
      if not entry:
        return flight_pb2.Receipt(
            succeed=False,
            message='Flight id {0} is not found.'.format(flight_data.id))
      if entry.next_index != flight_data.index:
        return flight_pb2.Receipt(
            succeed=False,
            message='Expect index {0} but received index {1}.'.format(
                entry.next_index, flight_data.index))

      entry.data += flight_data.data

    if flight_data.final:
      entry.next_index = -1
      entry.status = models.FlightDataStatus.UPLOADED
    else:
      entry.next_index = flight_data.index + 1
      entry.status = models.FlightDataStatus.UPLOADING
    entry.last_update = datetime.datetime.utcnow()
    entry.save()
    self.logger.info('Flight data saved.')

    return flight_pb2.Receipt(succeed=True)

  def CreateLogEntry(self, request, context):
    self.logger.info('Creating log entry for flight {0}...'.format(request.id))
    flight_data = models.FlightData.objects(flight_id=request.id).first()
    if not flight_data:
      raise Exception('Flight data {0} is not found.'.format(request.id))

    log_entry = analyzer.FlightDataAnalyzer().analyze(flight_data)
    self.logger.info('Created log entry:\n{0}'.format(repr(log_entry)))
    log_entry.save()
    self.logger.info('Log entry saved.')

    response = flight_pb2.CreateLogEntryResponse()
    response.succeed = True
    response.departure_airport = log_entry.get_field_value(
        essential.DepartureAirport.id())
    response.arrival_airport = log_entry.get_field_value(
        essential.ArrivalAirport.id())
    response.route = log_entry.get_field_value(essential.Route.id())
    response.total_time = log_entry.get_field_value(
        essential.TotalTime.id()).total_seconds() / 3600.0
    response.total_landings = log_entry.get_field_value(
        essential.DayLanding.id(),
        default_value=0) + log_entry.get_field_value(
            essential.NightLanding.id(), default_value=0)
    return response

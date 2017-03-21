import datetime

from flightdata import flight_pb2
from flightdata import flight_pb2_grpc
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

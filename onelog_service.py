import grpc
import time

from concurrent import futures
from google.apputils import app as gapp

from common import app
from flightdata import flight_pb2_grpc
from onelog.services import flight_service


class ServiceApp(app.App):
  def run(self):
    self.init_logging('../logs/onelog_service')

    self.logger.info('Starting GRPC server...')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    flight_pb2_grpc.add_FlightServiceServicer_to_server(
      flight_service.FlightService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    self.logger.info('GRPC server started.')

    while True:
      time.sleep(1)


def main(unused_argv):
  app = ServiceApp('service')
  return app.run()

if __name__ == "__main__":
  gapp.run()


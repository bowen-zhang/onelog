import geopy
import io
import logging

from common import pattern
from common import unit
from flightdata import io as flightdata_io
from flightdata import definitions
from onelog.core import analyzer
from onelog.core import engine
from onelog.core import essential
from onelog.core import models


def main():
  flight_data = models.FlightData.objects.order_by('-last_update').first()
  if flight_data == None:
    print 'No flight data to analyze.'
    return

  log_entry = analyzer.FlightDataAnalyzer().analyze(flight_data)
  print repr(log_entry)


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  main()

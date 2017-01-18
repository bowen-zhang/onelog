import datetime
import ephem

from common import unit
from onelog.core import models


def get_distance(airport1_code, airport2_code):
	try:
		airport1 = models.Airport.objects.get(icao_id=airport1_code)
		airport2 = models.Airport.objects.get(icao_id=airport2_code)
		return airport1.geolocation - airport2.geolocation
	except:
		return None

def get_civil_twilight_time(date, geolocation):
	observer = ephem.Observer()
	observer.pressure = 0
	observer.horizon = '-6'
	observer.lat = str(geolocation.latitude.degree)
	observer.lon = str(geolocation.longitude.degree)
	observer.elevation = geolocation.elevation.meter
	observer.date = datetime.datetime(date.year, date.month, date.day)
	sun = ephem.Sun()
	dawn = observer.next_rising(sun, use_center=True).tuple()
	dawn = datetime.datetime(dawn[0], dawn[1], dawn[2], dawn[3], dawn[4], int(dawn[5]))
	dusk = observer.next_setting(sun, use_center=True).tuple()
	dusk = datetime.datetime(dusk[0], dusk[1], dusk[2], dusk[3], dusk[4], int(dusk[5]))

	return (dawn, dusk)

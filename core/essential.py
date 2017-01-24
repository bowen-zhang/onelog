import datetime

from common import unit
from onelog.core import engine
from onelog.core import models
from onelog.util import utility


@engine.register
class Date(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Date', data_type=models.LogEntryFieldDataType.DATE)


@engine.register
class TailNumber(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Tail Number', data_type=models.LogEntryFieldDataType.SHORT_TEXT)


@engine.register
class DepartureAirport(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='From', data_type=models.LogEntryFieldDataType.SHORT_TEXT)


@engine.register
class ArrivalAirport(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='To', data_type=models.LogEntryFieldDataType.SHORT_TEXT)


@engine.register
class Route(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Route', data_type=models.LogEntryFieldDataType.SHORT_TEXT)


@engine.register
class TimeOut(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Time Out', data_type=models.LogEntryFieldDataType.DATETIME)


@engine.register
class TimeIn(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Time In', data_type=models.LogEntryFieldDataType.DATETIME)


@engine.register
class TachOut(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Tach Out', data_type=models.LogEntryFieldDataType.FLOAT)


@engine.register
class TachIn(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Tach In', data_type=models.LogEntryFieldDataType.FLOAT)


@engine.register
class HobbsOut(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Hobbs Out', data_type=models.LogEntryFieldDataType.FLOAT)


@engine.register
class HobbsIn(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Hobbs In', data_type=models.LogEntryFieldDataType.FLOAT)


@engine.register
class SimulatedInstrumentTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Simulated Instrument Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)


@engine.register
class ActualInstrumentTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Actual Instrument Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)


@engine.register
class TotalTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Total Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([TimeOut, TimeIn])
	def compute(self, context, time_out, time_in):
		return time_in - time_out


@engine.register
class PicTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='PIC Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([TotalTime])
	def compute(self, context, total_time):
		if context.current_participant:
			return total_time
		else:
			return None


@engine.register
class TotalDistance(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Total Distance', data_type=models.LogEntryFieldDataType.FLOAT)

	@engine.require([DepartureAirport, ArrivalAirport])
	def compute(self, context, departure_airport, arrival_airport):
		route = context.get_field_value(Route)

		prev = None
		distance = unit.Length()
		try:
			prev = models.Airport.objects.get(icao_id=departure_airport)
		except:
			return None

		waypoints = (route.split(' ') if route else []) + [arrival_airport]
		for waypoint in waypoints:
			try:
				current = models.Airport.objects.get(icao_id=waypoint)
				distance += current.geolocation - prev.geolocation
				prev = current
			except:
				pass

		return distance.nautical_mile


@engine.register
class MaxDistance(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Max Distance', data_type=models.LogEntryFieldDataType.FLOAT)

	@engine.require([DepartureAirport, ArrivalAirport])
	def compute(self, context, departure_airport, arrival_airport):
		route = context.get_field_value(Route)

		start = None
		max_distance = unit.Length()
		try:
			start = models.Airport.objects.get(icao_id=departure_airport)
		except:
			return None

		waypoints = (route.split(' ') if route else []) + [arrival_airport]
		for waypoint in waypoints:
			try:
				current = models.Airport.objects.get(icao_id=waypoint)
				distance = current.geolocation - start.geolocation
				if distance.meter > max_distance.meter:
					max_distance = distance
			except:
				pass

		return max_distance.nautical_mile

@engine.register
class CrossCountryTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, TotalTime])
	def compute(self, context, max_distance, total_time):
		if max_distance > 0:
			return total_time
		else:
			return None

@engine.register
class CrossCountryTime15nm(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country (15nm) Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, TotalTime])
	def compute(self, context, max_distance, total_time):
		if max_distance > 15:
			return total_time
		else:
			return None

@engine.register
class CrossCountryTime25nm(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country (25nm) Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, TotalTime])
	def compute(self, context, max_distance, total_time):
		if max_distance > 25:
			return total_time
		else:
			return None

@engine.register
class CrossCountryTime50nm(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country (50nm) Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, TotalTime])
	def compute(self, context, max_distance, total_time):
		if max_distance > 50:
			return total_time
		else:
			return None

@engine.register
class NightTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Night Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([DepartureAirport, ArrivalAirport, TimeOut, TimeIn])
	def compute(self, context, departure_airport, arrival_airport, time_out, time_in):
		time = datetime.timedelta()

		departure_geolocation = None
		arrival_geolocation = None
		try:
			departure_geolocation = models.Airport.objects.get(icao_id=departure_airport).geolocation
			arrival_geolocation = models.Airport.objects.get(icao_id=arrival_airport).geolocation
		except:
			return None

		date_out = time_out.date()
		date_in = time_in.date()
		one_day = datetime.timedelta(days=1)

		(dawn, dusk) = utility.get_civil_twilight_time(date_out, departure_geolocation)
		if dawn < dusk:
			if time_out < dawn:
				end_of_day = datetime.combine(date_out + one_day, datetime.time())
				time += (dawn - timeout) + (end_of_day - dusk)
			elif time_out < dusk: # 
				time += end_of_day - dusk
			else:
				time += end_of_day - timeout
		else:
			if time_out < dusk:
				time += dawn - dusk
			elif time_out < dawn:
				time += dawn - time_out

		date = date_out + one_day
		while date <= date_in:
			(dawn, dusk) = utility.get_civil_twilight_time(date, arrival_geolocation)
			if dawn < dusk:
				time += dawn - datetime.combine(date, datetime.time())
				time += datetime.combine(date + one_day, datetime.time()) - dusk
			else:
				time += dawn - dusk
			date += one_day

		(dawn, dusk) = utility.get_civil_twilight_time(date_in, arrival_geolocation)
		if dawn < dusk:
			if time_in < dawn:
				end_of_day = datetime.combine(date_out + one_day, datetime.time())
				time -= (dawn - time_in) + (end_of_day - dusk)
			elif time_in < dusk: # 
				time -= end_of_day - dusk
			else:
				time -= end_of_day - time_in
		else:
			if time_in < dusk:
				time -= dawn - dusk
			elif time_in < dawn:
				time -= dawn - time_in

		return time if time.total_seconds()>0 else None


@engine.register
class DayTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Day Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([TotalTime, NightTime])
	def compute(self, context, total_time, night_time):
		return total_time - night_time


@engine.register
class CrossCountryNightTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country Night Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, NightTime])
	def compute(self, context, max_distance, night_time):
		if max_distance > 0:
			return night_time
		else:
			return None

@engine.register
class CrossCountryNightTime15nm(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country (15nm) Night Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, NightTime])
	def compute(self, context, max_distance, night_time):
		if max_distance > 15:
			return night_time
		else:
			return None

@engine.register
class CrossCountryNightTime25nm(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country (25nm) Night Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, NightTime])
	def compute(self, context, max_distance, night_time):
		if max_distance > 25:
			return night_time
		else:
			return None

@engine.register
class CrossCountryNightTime50nm(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Cross Country (50nm) Night Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([MaxDistance, NightTime])
	def compute(self, context, max_distance, night_time):
		if max_distance > 50:
			return night_time
		else:
			return None


@engine.register
class DualReceivedTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Dual Received', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([TotalTime])
	def compute(self, context, total_time):
		instructor = [x for x in context.participants if x != context.current_participant and x.role == models.ParticipantRole.INSTRUCTOR]
		if instructor:
			return total_time
		else:
			return None


@engine.register
class DualGivenTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Dual Given', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([TotalTime], participant_role=models.ParticipantRole.INSTRUCTOR)
	def compute(self, context, total_time):
		pilot_roles = [models.ParticipantRole.STUDENT, models.ParticipantRole.PILOT, models.ParticipantRole.INSTRUCTOR]
		other_pilots = [x for x in context.participants if x != context.current_participant and x.role in pilot_roles]
		if other_pilots:
			return total_time


@engine.register
class SoloTime(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Solo Time', data_type=models.LogEntryFieldDataType.TIMEDELTA)

	@engine.require([TotalTime])
	def compute(self, context, total_time):
		if not context.current_participant:
			return None

		if len(context.participants) == 1:
			return total_time
		else:
			return None


@engine.register
class DayLanding(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Landing (Day)', data_type=models.LogEntryFieldDataType.INTEGER)


@engine.register
class NightLanding(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Landing (Night)', data_type=models.LogEntryFieldDataType.INTEGER)


@engine.register
class Holds(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Holds', data_type=models.LogEntryFieldDataType.INTEGER)


class Approach(object):
	def __init__(self, airport, approach_type, runway):
		self._airport = airport
		self._approach_type = approach_type
		self._runway = runway

	@property
	def airport(self):
		return self._airport

	@property
	def approach_type(self):
		return self._approach_type
	
	@property
	def runway(self):
		return self._runway

	@classmethod
	def deserialize(cls, dict):
		return Approach(dict['_airport'], dict['_approach_type'], dict['_runway'])


@engine.register
class Approaches(models.ObjectLogEntryFieldType):
	def __init__(self):
		models.ObjectLogEntryFieldType.__init__(self, display_name='Approaches', object_cls=Approach)


@engine.register
class Remarks(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Remarks', data_type=models.LogEntryFieldDataType.LONG_TEXT)


@engine.register
class FlightReview(models.BasicLogEntryFieldType):
	def __init__(self):
		models.BasicLogEntryFieldType.__init__(self, display_name='Flight Review', data_type=models.LogEntryFieldDataType.BOOLEAN)

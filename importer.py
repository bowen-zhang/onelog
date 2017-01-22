import abc
import datetime
import threading
import time
import sys
import Queue

from onelog.core import engine
from onelog.core import essential
from onelog.core import loader
from onelog.core import models

class DataImporter(loader.DataLoader):
	MAX_COMMIT_SIZE = 10000

	def __init__(self, kind, model, filename, delimiter=',', commit=True):
		super(DataImporter, self).__init__(filename, delimiter)

		self._kind = kind
		self._model = model
		self._commit = commit
		self._queue = Queue.Queue(DataImporter.MAX_COMMIT_SIZE*2)
		self._total_read = 0
		self._total_parsed = 0
		self._total_imported = 0

		cls = type(self)
		self._field_names = [x for x in dir(cls) if isinstance(getattr(cls, x), loader.DataColumn) and not x.startswith('_')]

	def reset(self):
		if self._commit:
			print('Deleting existing %s data...' % (self._kind))
			self._model.drop_collection()

	def load(self):

		if self._commit:
			load_complete = threading.Event()
			import_thread = threading.Thread(target=self._import_data, args=(load_complete,))
			import_thread.daemon = True
			import_thread.start()

		import_complete = threading.Event()
		monitor_thread = threading.Thread(target=self._show_progress, args=(import_complete,))
		monitor_thread.daemon = True
		monitor_thread.start()

		try:
			super(DataImporter, self).load(self.on_data)
		finally:
			if self._commit:
				load_complete.set()
				import_thread.join()
			import_complete.set()
			monitor_thread.join()

	def on_data(self, _):
		self._total_read +=1
		doc = self.parse()
		if doc:
			self._total_parsed += 1
		else:
			#print 'Line {0} is dropped.'.format(self.line_number)
			pass
		if doc and self._commit:
			self._queue.put(doc, block=True)

	def parse(self):
		doc = self._model()
		for field_name in self._field_names:
			value = getattr(self, field_name)
			setattr(doc, field_name, value)
		return doc

	def _import_data(self, complete_signal):
		while not complete_signal.is_set() or not self._queue.empty():
			while not complete_signal.is_set() and self._queue.qsize() < DataImporter.MAX_COMMIT_SIZE/3:
				time.sleep(0.5)	

			buffer = []
			while not self._queue.empty() and len(buffer) < DataImporter.MAX_COMMIT_SIZE:
				buffer.append(self._queue.get())
			if buffer:
				self._model.objects.insert(buffer, load_bulk=False)
				self._total_imported += len(buffer)
			

	def _show_progress(self, complete_signal):
		start = datetime.datetime.now()
		while not complete_signal.is_set():
			total_seconds = (datetime.datetime.now() - start).total_seconds()
			msg = '\r{0:.0f}% Done (queue={1}) ({2:.2f} entities/sec)   '.format(
				self.progress*100, 
				self._queue.qsize(), 
				self._total_parsed/total_seconds if total_seconds>0 else 0)
			sys.stdout.write(msg)
			sys.stdout.flush()
			time.sleep(1)

		print('')
		print('Total read: {0}'.format(self._total_read))
		print('Total parsed: {0}'.format(self._total_parsed))
		print('Total imported: {0}'.format(self._total_imported))


class DataImporterException(Exception):
	pass


class EngineDataImporter(DataImporter):
	# CSV Example:
	# CODE,MFR,MODEL,TYPE,HORSEPOWER,THRUST,
	# 41514,LYCOMING  ,O&VO-360 SER ,1 ,00180,000000,
	code = loader.IntColumn('CODE')
	manufacturer = loader.StringColumn('MFR')
	model = loader.StringColumn('MODEL')
	type = loader.EnumColumn('TYPE', enum_type=models.EngineType)
	horsepower = loader.IntColumn('HORSEPOWER')
	thrust = loader.IntColumn('THRUST')

	def __init__(self, commit=True):
		super(EngineDataImporter, self).__init__('Engine', models.EngineModel, 'data/ENGINE.txt', commit=commit)


def normalize_aircraft_model_code(code):
	id = 0
	for ch in code:
		if ch >= '0' and ch <= '9':
			id += id * 36 + (ord(ch) - ord('0'))
		elif ch >= 'A' and ch <= 'Z':
			id += id * 36 + (ord(ch) - ord('A') + 10)
		else:
			raise Exception('invalid code: %s' % (code))
	return id


class AircraftModelImporter(DataImporter):
	# CSV Example:
	# CODE,MFR,MODEL,TYPE-ACFT,TYPE-ENG,AC-CAT,BUILD-CERT-IND,NO-ENG,NO-SEATS,AC-WEIGHT,SPEED,
	# 7102807,PIPER,PA-28-181,4,1 ,1,0,01,004,CLASS 1,0105,
	builder_certification = loader.EnumColumn('BUILD-CERT-IND', enum_type=models.BuilderCertification)
	code = loader.IntColumn('CODE', preprocessor=normalize_aircraft_model_code)
	manufacturer = loader.StringColumn('MFR')
	model = loader.StringColumn('MODEL')
	aircraft_type = loader.EnumColumn('TYPE-ACFT', enum_type=models.AircraftType)
	engine_type = loader.EnumColumn('TYPE-ENG', enum_type=models.EngineType)
	category = loader.EnumColumn('AC-CAT', enum_type=models.AircraftCategory)
	builder_certification = builder_certification
	number_of_engines = loader.IntColumn('NO-ENG')
	number_of_seats = loader.IntColumn('NO-SEATS')
	weight_category = loader.EnumColumn('AC-WEIGHT', enum_type=models.AircraftWeightCategory, preprocessor=lambda x: x[6:])
	speed = loader.IntColumn('SPEED')
	
	def __init__(self, commit=True):
		super(AircraftModelImporter, self).__init__('Aircraft Model', models.AircraftModel, 'data/ACFTREF.txt', commit=commit)


def lats_lons_to_geopt(lats, lons):
	lat = float(lats[0:-1])/3600 * (-1 if lats[-1] == 'S' else 1)
	lon = float(lons[0:-1])/3600 * (-1 if lons[-1] == 'W' else 1)
	return [lon, lat]


class AirportImporter(DataImporter):
	# CSV Example:
	# "SiteNumber"	"Type"	"LocationID"	"EffectiveDate"	"Region"	"DistrictOffice"	"State"	"StateName"	"County"	"CountyState"	"City"	"FacilityName"	"Ownership"	"Use"	"Owner"	"OwnerAddress"	"OwnerCSZ"	"OwnerPhone"	"Manager"	"ManagerAddress"	"ManagerCSZ"	"ManagerPhone"	"ARPLatitude"	"ARPLatitudeS"	"ARPLongitude"	"ARPLongitudeS"	"ARPMethod"	"ARPElevation"	"ARPElevationMethod"	"MagneticVariation"	"MagneticVariationYear"	"TrafficPatternAltitude"	"ChartName"	"DistanceFromCBD"	"DirectionFromCBD"	"LandAreaCoveredByAirport"	"BoundaryARTCCID"	"BoundaryARTCCComputerID"	"BoundaryARTCCName"	"ResponsibleARTCCID"	"ResponsibleARTCCComputerID"	"ResponsibleARTCCName"	"TieInFSS"	"TieInFSSID"	"TieInFSSName"	"AirportToFSSPhoneNumber"	"TieInFSSTollFreeNumber"	"AlternateFSSID"	"AlternateFSSName"	"AlternateFSSTollFreeNumber"	"NOTAMFacilityID"	"NOTAMService"	"ActiviationDate"	"AirportStatusCode"	"CertificationTypeDate"	"FederalAgreements"	"AirspaceDetermination"	"CustomsAirportOfEntry"	"CustomsLandingRights"	"MilitaryJointUse"	"MilitaryLandingRights"	"InspectionMethod"	"InspectionGroup"	"LastInspectionDate"	"LastOwnerInformationDate"	"FuelTypes"	"AirframeRepair"	"PowerPlantRepair"	"BottledOxygenType"	"BulkOxygenType"	"LightingSchedule"	"BeaconSchedule"	"ATCT"	"UNICOMFrequencies"	"CTAFFrequency"	"SegmentedCircle"	"BeaconColor"	"NonCommercialLandingFee"	"MedicalUse"	"SingleEngineGA"	"MultiEngineGA"	"JetEngineGA"	"HelicoptersGA"	"GlidersOperational"	"MilitaryOperational"	"Ultralights"	"OperationsCommercial"	"OperationsCommuter"	"OperationsAirTaxi"	"OperationsGALocal"	"OperationsGAItin"	"OperationsMilitary"	"OperationsDate"	"AirportPositionSource"	"AirportPositionSourceDate"	"AirportElevationSource"	"AirportElevationSourceDate"	"ContractFuelAvailable"	"TransientStorage"	"OtherServices"	"WindIndicator"	"IcaoIdentifier"	"BeaconSchedule"
	# 02022.*A	AIRPORT	'PAO	03/31/2016	AWP	SFO	CA	CALIFORNIA	SANTA CLARA	CA	PALO ALTO	PALO ALTO	PU	PU	CITY OF PALO ALTO	250 HAMILTON AVENUE	PALO ALTO, CA 94301-2531	  (650) 329-2688	ANDREW SWANSON	1925 EMBARCADERO ROAD	PALO ALTO, CA 94301-2531	  (650) 329-2444	37-27-40.0000N	134860.0000N	122-06-54.2000W	439614.2000W	E	6	E	15E	1995		SAN FRANCISCO	0	E	  102	ZOA	ZCO	OAKLAND				N	OAK	OAKLAND		1-800-WX-BRIEF				PAO	Y	04/01/1940	O		NGY	NO OBJECTION	N	N	N	Y	S	S	05072015		100LLA	MAJOR	MAJOR	LOW		SEE RMK	SS-SR	Y	122.950	118.600	Y	CG	N		170	18	1	1	1					105	115083	76509		05/05/2015	NGS	2001-04-13 00:00:00.0				TIE	AMB,AVNCS,CHTR,GLD,INSTR,RNTL,SALES,SURV	Y-L	KPAO	SS-SR
	icao_id = loader.StringColumn('IcaoIdentifier')
	location_id = loader.StringColumn('LocationID', preprocessor=lambda x: x.lstrip('\''))
	airport_type = loader.EnumColumn('Type', enum_type=models.AirportType, preprocessor=lambda x: x.replace(' ', '_'))
	city = loader.StringColumn('City')
	state = loader.StringColumn('State')
	latitude = loader.FloatColumn('ARPLatitudeS', preprocessor=lambda x: float(x[0:-1])/3600 * (-1 if x[-1] == 'S' else 1))
	longitude = loader.FloatColumn('ARPLongitudeS', preprocessor=lambda x: float(x[0:-1])/3600 * (-1 if x[-1] == 'W' else 1))
	elevation = loader.IntColumn('ARPElevation')

	def __init__(self, commit=True):
		super(AirportImporter, self).__init__('Airport', models.Airport, 'data/NfdcFacilities.txt', delimiter='\t', commit=commit)

	def parse(self):
		if self.airport_type != models.AirportType.AIRPORT:
			return None

		airport = models.Airport()
		airport.icao_id = self.icao_id or self.location_id
		airport.airport_type = self.airport_type
		airport.city = self.city
		airport.state = self.state
		airport.location = [self.longitude, self.latitude]
		airport.elevation = self.elevation
		return airport		


class AircraftImporter(DataImporter):
	# CSV Example:
	# N-NUMBER,SERIAL NUMBER,MFR MDL CODE,ENG MFR MDL,YEAR MFR,TYPE REGISTRANT,NAME,STREET,STREET2,CITY,STATE,ZIP CODE,REGION,COUNTY,COUNTRY,LAST ACTION DATE,CERT ISSUE DATE,CERTIFICATION,TYPE AIRCRAFT,TYPE ENGINE,STATUS CODE,MODE S CODE,FRACT OWNER,AIR WORTH DATE,OTHER NAMES(1),OTHER NAMES(2),OTHER NAMES(3),OTHER NAMES(4),OTHER NAMES(5),EXPIRATION DATE,UNIQUE ID,KIT MFR, KIT MODEL,MODE S CODE HEX,
	# 2112K,28-7990234                    ,7102807,41514,1978,8,DREAM OF FLIGHT INC                               ,22669 NE ALDER CREST DR UNIT 201 ,                                 ,REDMOND           ,WA,980535869 ,S,033,US,20131125,20100512,1NU       ,4,1 ,V ,50337741, ,19781213,                                                  ,                                                  ,                                                  ,                                                  ,                                                  ,20170430,00081722,                              ,                    ,A1BFE1    ,
	tail_number = loader.StringColumn('N-NUMBER', preprocessor=lambda x: 'N' + x)
	serial_number = loader.StringColumn('SERIAL NUMBER')
	aircraft_model_code = loader.IntColumn('MFR MDL CODE', preprocessor=normalize_aircraft_model_code)
	engine_model_code = loader.IntColumn('ENG MFR MDL')
	year = loader.IntColumn('YEAR MFR')
	registrant_type = loader.EnumColumn('TYPE REGISTRANT', enum_type=models.RegistrantType)
	owner = loader.StringColumn('NAME')
	owner_address = loader.Container(models.Address, dict(
		street = loader.StringColumn('STREET'),
		street2 = loader.StringColumn('STREET2'),
		city = loader.StringColumn('CITY'),
		state = loader.StringColumn('STATE'),
		zipcode = loader.StringColumn('ZIP CODE'),
		))

	certificate_issue_date = loader.DateTimeColumn('CERT ISSUE DATE', fmt='%Y%m%d')
	airworthiness_date = loader.DateTimeColumn('AIR WORTH DATE', fmt='%Y%m%d')
	expiration_date = loader.DateTimeColumn('EXPIRATION DATE', fmt='%Y%m%d')

	def __init__(self, commit=True):
		super(AircraftImporter, self).__init__('Aircraft', models.Aircraft, 'data/MASTER.txt', commit=commit)


def airman_unique_id_normalizer(id):
	return str(ord(id[0]) - ord('A')) + id[1:]

class AirmanImporter(DataImporter):
	unique_id = loader.IntColumn('UNIQUE ID', preprocessor = airman_unique_id_normalizer)
	first_name = loader.StringColumn('FIRST NAME')
	last_name = loader.StringColumn('LAST NAME')
	address = loader.Container(models.Address, dict(
		street = loader.StringColumn('STREET 1'),
		street2 = loader.StringColumn('STREET 2'),
		city = loader.StringColumn('CITY'),
		state = loader.StringColumn('STATE'),
		zipcode = loader.StringColumn('ZIP CODE'),
		country = loader.StringColumn('COUNTRY'),
		))
	medical_certificate = loader.Container(models.MedicalCertificate, dict(
		certificate_class = loader.EnumColumn('MED CLASS', enum_type=models.MedicalCertificateClass),
		examination_date = loader.DateTimeColumn('MED DATE', fmt='%m%Y'),
		expiration_date = loader.DateTimeColumn('MED EXP DATE', fmt='%m%Y'),
		))

	def __init__(self, commit=True):
		super(AirmanImporter, self).__init__('Pilot', models.Person, 'data/PILOT_BASIC.csv', commit=commit)
		self._cert_loader = AirmanCertImporter()
		self._cert_loader.__enter__()
		self._cert_loader.next()

	def parse(self):
		person = super(AirmanImporter, self).parse()
		if not person.medical_certificate:
			return None

		person.airman_certificates = []

		while self._cert_loader.has_data() and self.unique_id > self._cert_loader._unique_id:
			self._cert_loader.next()
		while self._cert_loader.has_data() and self.unique_id == self._cert_loader._unique_id:
			person.airman_certificates += self._cert_loader.parse()
			self._cert_loader.next()
		
		if not person.airman_certificates:
			return None

		return person


class AirmanCertImporter(DataImporter):
	_unique_id = loader.IntColumn('UNIQUE ID', preprocessor = airman_unique_id_normalizer)

	type = loader.EnumColumn('TYPE', enum_type=models.AirmanCertificateType, preprocessor=lambda x: ord(x) if x else None)
	level = loader.EnumColumn('LEVEL', enum_type=models.AirmanCertificateLevel, preprocessor=lambda x: ord(x) if x else None)
	expiration_date = loader.DateTimeColumn('EXPIRE DATE', fmt='%m%d%Y')

	_airman_cert_rating_columns = ['RATING' + str(i) for i in range(1,12)]
	_airman_cert_type_rating_columns = ['TYPERATING' + str(i) for i in range(1,100)]
	_airman_cert_rating_map = {
	    'ASE':   models.AirmanCertificateRating.AIRPLANE_SINGLE_ENGINE,
	    'ASEL':  models.AirmanCertificateRating.AIRPLANE_SINGLE_ENGINE_LAND,
	    'ASES':  models.AirmanCertificateRating.AIRPLANE_SINGLE_ENGINE_SEA,
	    'AME':   models.AirmanCertificateRating.AIRPLANE_MULTIENGINE,
	    'AMEL':  models.AirmanCertificateRating.AIRPLANE_MULTIENGINE_LAND,
	    'AMES':  models.AirmanCertificateRating.AIRPLANE_MULTIENGINE_SEA,
	    'HEL':   models.AirmanCertificateRating.HELICOPTER,
	    'INSTA': models.AirmanCertificateRating.INSTRUMENT_AIRPLANE,
	    'INSTH': models.AirmanCertificateRating.INSTRUMENT_HELICOPTER,
	}

	def __init__(self, commit=True):
		super(AirmanCertImporter, self).__init__('Pilot Cert', models.AirmanCertificate, 'data/PILOT_CERT.csv', commit=commit)

	def parse(self):
		fields = self.to_dict()
		certs = []
		for column in AirmanCertImporter._airman_cert_rating_columns:
			rating_str = fields[column]
			if not rating_str:
				break
			rating = self._string_to_airman_cert_rating(rating_str[2:])
			if not rating:
				continue
				
			airman_cert = models.AirmanCertificate()
			airman_cert.type = self.type
			airman_cert.level = self.level
			airman_cert.expiration_date = self.expiration_date
			airman_cert.rating = rating
			certs.append(airman_cert)

		for column in AirmanCertImporter._airman_cert_type_rating_columns:
			type_rating = fields[column]
			if not type_rating:
				break
			airman_cert = models.AirmanCertificate()
			airman_cert.type = self.type
			airman_cert.level = self.level
			airman_cert.expiration_date = self.expiration_date
			airman_cert.type_rating = type_rating[2:]
			certs.append(airman_cert)

		return certs

	def _string_to_airman_cert_rating(self, str):
		if str in AirmanCertImporter._airman_cert_rating_map:
			return AirmanCertImporter._airman_cert_rating_map[str]
		else:
			return None


def name_to_airman_id(name):
	if not name:
		return None

	parts = name.split(' ')
	if len(parts) != 2:
		return None

	(first, last) = parts
	try:
		person = models.Person.objects.get(first_name=first.upper(), last_name=last.upper())
		return person.unique_id
	except:
		return None


def hours_to_timedelta(hours):
	return datetime.timedelta(hours=float(hours)) if hours else None	

def approach_loader(str):
	if not str:
		return None
	fields = str.split(';')
	return essential.Approach(airport=fields[3], approach_type=fields[1], runway=fields[2])


class LogTenProImporter(DataImporter):
	date = loader.DateTimeColumn('Date', fmt='%Y-%m-%d')
	tail_number = loader.StringColumn('Aircraft ID')
	departure_airport = loader.StringColumn('From')
	arrival_airport = loader.StringColumn('To')
	route = loader.StringColumn('Route', preprocessor=lambda x: x.replace('-', ' '))
	time_out = loader.TimeColumn('Out', fmt='%H%M')
	time_in = loader.TimeColumn('In', fmt='%H%M')
	tach_out = loader.FloatColumn('Tach Out')
	tach_in = loader.FloatColumn('Tach In')
	sim_inst = loader.TimeDeltaColumn('Sim Inst', preprocessor=hours_to_timedelta)
	actual_inst = loader.TimeDeltaColumn('Actual Inst', preprocessor=hours_to_timedelta)
	pic = loader.IntColumn('PIC/P1 Crew', preprocessor=name_to_airman_id)
	instructor = loader.IntColumn('Instructor', preprocessor=name_to_airman_id)
	student = loader.IntColumn('Student', preprocessor=name_to_airman_id)
	dual_recv = loader.TimeDeltaColumn('Dual Rcvd', preprocessor=hours_to_timedelta)
	dual_given = loader.TimeDeltaColumn('Dual Given', preprocessor=hours_to_timedelta)
	day_landing = loader.IntColumn('Day Ldg')
	night_landing = loader.IntColumn('Night Ldg')
	student_day_landing = loader.IntColumn('Student Day Ldg')
	student_night_landing = loader.IntColumn('Student Day Ldg')
	holds = loader.IntColumn('Holds')
	remarks = loader.StringColumn('Remarks')
	approach1 = loader.CustomColumn('Approach 1', loader=approach_loader)
	approach2 = loader.CustomColumn('Approach 2', loader=approach_loader)
	approach3 = loader.CustomColumn('Approach 3', loader=approach_loader)
	approach4 = loader.CustomColumn('Approach 4', loader=approach_loader)
	approach5 = loader.CustomColumn('Approach 5', loader=approach_loader)
	approach6 = loader.CustomColumn('Approach 6', loader=approach_loader)

	#Date	Aircraft ID	Aircraft Type	From	Route	To	Out	In	Tach Out	Tach In	Total Time	Multi-Engine	PIC	SIC	Solo	Night	XC	XC Night	Sim Inst	Actual Inst	Dual Rcvd	Dual Given	Sim Inst Given	Act Inst Given	Ground	Student Time	AATD	PIC/P1 Crew	SIC/P2 Crew	Instructor	Safety Pilot	Student	Examiner	Day Ldg	Night Ldg	Student Day Ldg	Student Night Ldg	Holds	Approach 1	Approach 2	Approach 3	Approach 4	Approach 5	Approach 6	Passenger 01	Passenger 02	Passenger 03	Remarks	Student Note	Self Review	Flight Review	Oil Added	Fuel Burned	Fuel Service

	def __init__(self, commit=True):
		super(LogTenProImporter, self).__init__('Log Entry', models.LogEntry, 'data/LogTenExport.txt', delimiter='\t', commit=commit)
		self._compute_engine = engine.ComputeEngine()

	def parse(self):
		if not self.date or not self.tail_number:
			return None

		if self.tail_number == 'GROUND':
			return self.parse_ground_log()
		else:
			return self.parse_flight_log()

	def parse_ground_log(self):
		entry = models.LogEntry()
		entry.type = models.LogEntryType.GROUND_LESSON
		entry.participants = []
		if self.pic:
			participant = models.Participant()
			participant.airman_id=self.pic
			participant.role = models.ParticipantRole.PILOT
			entry.participants.append(participant)
		if self.instructor:
			participant = models.Participant()
			participant.airman_id=self.instructor
			participant.role = models.ParticipantRole.INSTRUCTOR
			entry.participants.append(participant)
		if self.student:
			participant = models.Participant()
			participant.airman_id=self.instructor
			participant.role = models.ParticipantRole.INSTRUCTOR
			entry.participants.append(participant)
		return entry

	def parse_flight_log(self):
		if not self.departure_airport or not self.arrival_airport:
			return None

		self.time_out = datetime.datetime.combine(self.date, self.time_out) if self.time_out else None
		self.time_in = datetime.datetime.combine(self.date, self.time_in) if self.time_in else None
		if self.time_out and self.time_in and self.time_out > self.time_in:
			self.time_in += datetime.timedelta(days=1)

		entry = models.LogEntry()
		entry.type = models.LogEntryType.FLIGHT

		entry.add_field(essential.Date, self.date)
		entry.add_field(essential.TailNumber, self.tail_number)
		entry.add_field(essential.DepartureAirport, self.departure_airport)
		entry.add_field(essential.ArrivalAirport, self.arrival_airport)
		entry.add_field(essential.Route, self.route)
		entry.add_field(essential.TimeOut, self.time_out)
		entry.add_field(essential.TimeIn, self.time_in)
		entry.add_field(essential.TachOut, self.tach_out)
		entry.add_field(essential.TachIn, self.tach_in)
		entry.add_field(essential.ActualInstrumentTime, self.actual_inst)
		entry.add_field(essential.Remarks, self.remarks)

		entry.participants = []
		if self.pic:
			entry.add_field(essential.SimulatedInstrumentTime, self.sim_inst, self.pic)
			entry.add_field(essential.DualReceivedTime, self.dual_recv, self.pic)
			entry.add_field(essential.DualGivenTime, self.dual_given, self.pic)
			entry.add_field(essential.DayLanding, self.day_landing, self.pic)
			entry.add_field(essential.NightLanding, self.night_landing, self.pic)
			entry.add_field(essential.Holds, self.holds, self.pic)

			approaches= [self.approach1, self.approach2, self.approach3,
				self.approach4, self.approach5, self.approach6]
			approaches = [x for x in approaches if x]
			if approaches:
				entry.add_field(essential.Approaches, approaches, self.pic)

			participant = models.Participant()
			participant.airman_id=self.pic
			participant.role = models.ParticipantRole.PILOT
			entry.participants.append(participant)

		if self.instructor:
			entry.add_field(essential.DualGivenTime, self.dual_recv, self.instructor)

			participant = models.Participant()
			participant.airman_id=self.instructor
			participant.role = models.ParticipantRole.INSTRUCTOR
			entry.participants.append(participant)

		if self.student:
			entry.add_field(essential.DualReceivedTime, self.dual_given, self.student)
			entry.add_field(essential.DayLanding, self.student_day_landing, self.pic)
			entry.add_field(essential.NightLanding, self.student_night_landing, self.pic)

			participant = models.Participant()
			participant.airman_id=self.instructor
			participant.role = models.ParticipantRole.INSTRUCTOR
			entry.participants.append(participant)

		entry.created_at = datetime.datetime.now()
		entry.last_modified_at = entry.created_at

		self._compute_engine.compute(entry)


		return entry


if __name__ == "__main__":
	importer_types = [
		#EngineDataImporter, 
		#AircraftModelImporter,
		#AirportImporter,
		#AircraftImporter,
		#AirmanImporter,
		LogTenProImporter,
	]
	for importer_type in importer_types:
		with importer_type(commit=True) as importer:
			importer.reset()
			importer.load()
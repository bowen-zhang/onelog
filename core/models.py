# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import datetime
import enum
import json
import mongoengine
from mongoengine import fields

from common import unit
from onelog.core import extra_fields


mongoengine.connect('onelog')

builtin_list = list


class EngineType(enum.Enum):
    UNDEFINED = 0
    RECIPROCATING = 1
    TURBO_PROP = 2
    TURBO_SHAFT = 3
    TURBO_JET = 4
    TURBO_FAN = 5
    RAM_JET = 6
    TWO_CYCLE = 7
    FOUR_CYCLE = 8
    UNKNOWN = 9
    ELECTRIC = 10
    ROTARY = 11


class EngineModel(mongoengine.Document):
    code = fields.IntField()
    manufacturer = fields.StringField()
    model = fields.StringField()
    type = extra_fields.IntEnumField(EngineType)
    horsepower = fields.IntField()
    thrust = fields.IntField()

    meta = {
        'indexes': [
            'code',
            'manufacturer',
            'model',
            'type',
        ]
    }


class AircraftType(enum.Enum):
    GLIDER = 1
    BALLON = 2
    BLIMP = 3
    FIXED_WING_SINGLE_ENGINE = 4
    FIXED_WING_MULTI_ENGINE = 5
    ROTORCRAFT = 6
    WEIGHT_SHIFT_CONTROL = 7
    POWERED_PARACHUTE = 8
    GYROPLANE = 9


class AircraftCategory(enum.Enum):
    LAND = 1
    SEA = 2
    AMPHIBIAN = 3


class BuilderCertification(enum.Enum):
    TYPE_CERTIFIED = 0
    NOT_TYPE_CERTIFIED = 1
    LIGHT_SPORT = 2


class AircraftWeightCategory(enum.Enum):
    TO_12500 = 1
    FROM_12500_TO_20000 = 2
    FROM_20000 = 3
    UAV_UP_TO_55 = 4


class AircraftModel(mongoengine.Document):
    code = fields.IntField()
    manufacturer = fields.StringField()
    model = fields.StringField()
    aircraft_type = extra_fields.IntEnumField(AircraftType)
    engine_type = extra_fields.IntEnumField(EngineType)
    category = extra_fields.IntEnumField(AircraftCategory)
    builder_certification = extra_fields.IntEnumField(BuilderCertification)
    number_of_engines = fields.IntField()
    number_of_seats = fields.IntField()
    weight_category = extra_fields.IntEnumField(AircraftWeightCategory)
    speed = fields.IntField()

    meta = {
        'indexes': [
            'code',
            'manufacturer',
            'model',
            'aircraft_type',
            'engine_type',
            'category',
            ('aircraft_type', 'category'),
            'builder_certification',
        ]
    }


class RegistrantType(enum.Enum):
    INDIVIDUAL = 1
    PARTNERSHIP = 2
    CORPORATION = 3
    CO_OWNED = 4
    GOVERNMENT = 5
    NON_CITIZEN_CORPORATION = 8
    NON_CITIZEN_CO_OWNED = 9


class Address(mongoengine.EmbeddedDocument):
    street = fields.StringField()
    street2 = fields.StringField()
    city = fields.StringField()
    state = fields.StringField()
    zipcode = fields.StringField()
    country = fields.StringField()


class Aircraft(mongoengine.Document):
    tail_number = fields.StringField()
    serial_number = fields.StringField()
    aircraft_model_code = fields.IntField()
    engine_model_code = fields.IntField()
    year = fields.IntField()
    registrant_type = extra_fields.IntEnumField(RegistrantType)
    owner = fields.StringField()
    owner_address = fields.EmbeddedDocumentField(Address)
    certificate_issue_date = fields.DateTimeField()
    airworthiness_date = fields.DateTimeField()
    expiration_date = fields.DateTimeField()

    meta = {
        'indexes': [
            'tail_number',
            'aircraft_model_code',
            'engine_model_code',
            'registrant_type',
            'owner',
            'expiration_date',
        ]
    }


class AirportType(enum.Enum):
    AIRPORT = 1
    SEAPLANE_BASE = 2
    HELIPORT = 3
    GLIDERPORT = 4
    ULTRALIGHT = 5
    BALLOONPORT = 6


class Airport(mongoengine.Document):
    icao_id = fields.StringField()
    airport_type = extra_fields.IntEnumField(AirportType)
    city = fields.StringField()
    state = fields.StringField()
    location = fields.PointField()
    elevation = fields.IntField()

    meta = {
        'indexes': [
            'icao_id',
        ]
    }

    @property
    def geolocation(self):
        return unit.Geolocation(unit.Angle(self.location['coordinates'][0], unit.Angle.DEGREE, unit.Angle.LONGITUDE_RANGE), 
                                unit.Angle(self.location['coordinates'][1], unit.Angle.DEGREE, unit.Angle.LATITUDE_RANGE),
                                unit.Length(self.elevation, unit.Length.FOOT))


class MedicalCertificateClass(enum.Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3


class MedicalCertificate(mongoengine.EmbeddedDocument):
    certificate_class = extra_fields.IntEnumField(MedicalCertificateClass)
    examination_date = fields.DateTimeField()
    expiration_date = fields.DateTimeField()


class AirmanCertificateType(enum.Enum):
    PILOT = ord('P')
    PILOT_PART_61_75 = ord('Y')
    PILOT_PART_61_77 = ord('B')
    FLIGHT_INSTRUCTOR = ord('F')
    AUTHORIZED_AIRCRAFT_INSTRUCTOR = ord('A')
    GROUND_INSTRUCTOR = ord('G')
    FLIGHT_ENGINEER = ord('E')
    FLIGHT_ENGINEER_LESSEE = ord('H')
    FLIGHT_ENGINEER_FOREIGN = ord('X')
    MECHANIC = ord('M')
    CONTROL_TOWER_OPERATOR = ord('T')
    REPAIRMAN = ord('R')
    REPAIRMAN_EXPERIMENTAL_AIRCRAFT_BUILDER = ord('I')
    REMAIRMAN_LIGHT_SPORT_AIRCRAFT = ord('L')
    PARACHUTE_RIGGER = ord('W')
    DISPATCHER = ord('D')
    FLIGHT_NAVIGATOR = ord('N')
    FLIGHT_NAVIGATOR_FOREIGN = ord('J')
    FLIGHT_ATTENDANT = ord('Z')


class AirmanCertificateLevel(enum.Enum):
    AIRLINE_TRANSPORT_PILOT = ord('A')
    COMMERCIAL = ord('C')
    PRIVATE = ord('P')
    RECREATIONAL = ord('V')
    SPORT = ord('T')
    STUDENT = ord('S')

    FOREIGN_COMMERCIAL = ord('Z')
    FOREIGN_PRIVATE = ord('Y')
    HISTORIC = ord('X')

    AIRLINE_TRANSPORT_PILOT_LESSEE = ord('B')
    COMMERCIAL_LESSEE = ord('K')

    MASTER_PARACHUTE_RIGGER = ord('U')
    SENIOR_PARACHUTE_RIGGER = ord('W')


class AirmanCertificateRating(enum.Enum):
    AIRPLANE_SINGLE_ENGINE = 1
    AIRPLANE_SINGLE_ENGINE_LAND = 2
    AIRPLANE_SINGLE_ENGINE_SEA = 3

    AIRPLANE_MULTIENGINE = 10
    AIRPLANE_MULTIENGINE_LAND = 11
    AIRPLANE_MULTIENGINE_SEA = 12
    
    HELICOPTER = 20

    INSTRUMENT_AIRPLANE = 100
    INSTRUMENT_HELICOPTER = 101


class AirmanCertificate(mongoengine.EmbeddedDocument):
    type = extra_fields.IntEnumField(AirmanCertificateType)
    level = extra_fields.IntEnumField(AirmanCertificateLevel)
    rating = extra_fields.IntEnumField(AirmanCertificateRating)
    type_rating = fields.StringField()
    expiration_date = fields.DateTimeField()


class Person(mongoengine.Document):
    unique_id = fields.IntField()
    first_name = fields.StringField()
    last_name = fields.StringField()
    address = fields.EmbeddedDocumentField(Address)

    medical_certificate = fields.EmbeddedDocumentField(MedicalCertificate)
    airman_certificates = fields.ListField(fields.EmbeddedDocumentField(AirmanCertificate))

    meta = {
        'indexes': [
            'unique_id',
            ('first_name','last_name'),
            'medical_certificate.certificate_class',
            'medical_certificate.expiration_date',
            'airman_certificates.type',
            'airman_certificates.level',
            'airman_certificates.rating',
            'airman_certificates.expiration_date',
        ]
    }


class ComputeContext(object):
    def __init__(self, log_entry, current_participant):
        self._log_entry = log_entry
        self._current_participant = current_participant

    @property
    def log_entry(self):
        return self._log_entry
    
    @property
    def participants(self):
        return self._log_entry.participants
    
    @property
    def current_participant(self):
        return self._current_participant

    def get_field_value(self, field_type_cls):
        return self._log_entry.get_field_value(
            field_type_cls.id(),
            self._current_participant.airman_id if self._current_participant else None,
            default_to_shared=True)


class LogEntryFieldDataType(enum.Enum):
    INTEGER = 1
    FLOAT = 2
    SHORT_TEXT = 3
    LONG_TEXT = 4
    DATETIME = 5
    DATE = 6
    TIMEDELTA = 7
    OBJECT = 8


class LogEntryFieldType(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, display_name, is_hidden=False):
        self._display_name = display_name
        self._is_hidden = is_hidden

    @classmethod
    def id(cls):
        return hash(cls.__name__)

    @property
    def name(self):
        return type(self).__name__
    
    @property
    def display_name(self):
        return self._display_name

    @property
    def is_hidden(self):
        return self._is_hidden

    @abc.abstractmethod
    def to_string(self, value):
        raise NotImplementedError

    @abc.abstractmethod
    def from_string(self, raw_value):
        raise NotImplementedError

    def compute(self, context):
        return None

    def to_dict(self):
        return {
            'id': type(self).id(),
            'name': self.name,
            'display_name': self.display_name,
            'is_hidden': self.is_hidden,
            }


class BasicLogEntryFieldType(LogEntryFieldType):
    CONVERTERS = [
        (LogEntryFieldDataType.INTEGER, lambda x: int(x), lambda x: str(x)),
        (LogEntryFieldDataType.FLOAT, lambda x: float(x), lambda x: str(x)),
        (LogEntryFieldDataType.SHORT_TEXT, lambda x: x, lambda x: x),
        (LogEntryFieldDataType.LONG_TEXT, lambda x: x, lambda x: x),
        (LogEntryFieldDataType.DATETIME, lambda x: datetime.datetime.strptime(x, '%Y%m%d %H%M%S'), lambda x: '{:%Y%m%d %H%M%S}'.format(x)),
        (LogEntryFieldDataType.DATE, lambda x: datetime.datetime.strptime(x, '%Y%m%d').date(), lambda x: '{:%Y%m%d}'.format(x)),
        (LogEntryFieldDataType.TIMEDELTA, lambda x: datetime.timedelta(seconds=float(x)), lambda x: str(x.total_seconds())),
        ]

    def __init__(self, display_name, data_type, is_hidden=False):
        super(BasicLogEntryFieldType, self).__init__(display_name, is_hidden=is_hidden)
        converter = [x for x in BasicLogEntryFieldType.CONVERTERS if x[0]==data_type]
        if not converter:
            raise Exception('No converter found for type {0}'.format(data_type))
        converter = converter[0]        
        self._convert_from_string = converter[1]
        self._convert_to_string = converter[2]

    def to_string(self, value):
        if value is None:
            return None

        return self._convert_to_string(value)

    def from_string(self, raw_value):
        if not raw_value:
            return None

        return self._convert_from_string(raw_value)


class ObjectLogEntryFieldType(LogEntryFieldType):
    def __init__(self, display_name, object_cls, is_hidden=False):
        super(ObjectLogEntryFieldType, self).__init__(display_name, is_hidden=is_hidden)
        self._object_cls = object_cls

    def to_string(self, value):
        if value is None:
            return None

        if isinstance(value, list):
            return json.dumps([x.__dict__ for x in value])
        else:
            return json.dumps(value.__dict__)

    def from_string(self, raw_value):
        if raw_value is None:
            return None

        return json.loads(raw_value, object_hook=self._object_cls.deserialize)


class LogEntryFieldTypeFactory(object):
    _repository = {}

    @staticmethod
    def register(field_type_cls):
        LogEntryFieldTypeFactory._repository[field_type_cls.id()] = field_type_cls()

    @staticmethod
    def get(id):
        if id in LogEntryFieldTypeFactory._repository:
            return LogEntryFieldTypeFactory._repository[id]
        else:
            return None

    @staticmethod
    def get_all():
        return sorted(LogEntryFieldTypeFactory._repository.values(), key=lambda x: x.display_name)


class LogEntryField(mongoengine.EmbeddedDocument):

    type_id = fields.IntField()
    raw_value = fields.StringField()
    airman_id = fields.IntField()

    @property
    def value(self):
        field_type = LogEntryFieldTypeFactory.get(self.type_id)
        return field_type.from_string(self.raw_value)

    @value.setter
    def value(self, value):
        field_type = LogEntryFieldTypeFactory.get(self.type_id)
        self.raw_value = field_type.to_string(value)


class LogEntryType(enum.Enum):
    FLIGHT = 1
    GROUND_LESSON = 2


class ParticipantRole(enum.Enum):
    PILOT = 1
    PASSENGER = 2
    INSTRUCTOR = 3
    STUDENT = 4


class Participant(mongoengine.EmbeddedDocument):
    airman_id = fields.IntField()
    role = extra_fields.IntEnumField(ParticipantRole)

    signature = fields.StringField()
    date = fields.DateTimeField()


class LogEntryStatus(enum.Enum):
    LOCKED = 1
    PENDING = 2
    PENDING_DELETION = 3


class LogEntry(mongoengine.Document):
    type = extra_fields.IntEnumField(LogEntryType)

    participants = fields.EmbeddedDocumentListField(Participant)
    data_fields = fields.EmbeddedDocumentListField(LogEntryField)
    historical_data_fields = fields.EmbeddedDocumentListField(LogEntryField)

    created_by = fields.StringField()
    created_at = fields.DateTimeField()
    last_modified_at = fields.DateTimeField()

    status = extra_fields.IntEnumField(LogEntryStatus)
    
    def add_field(self, field_type_cls, value, airman_id=None):
        if not value:
            return

        field = LogEntryField()
        field.type_id = field_type_cls.id()
        field.airman_id = airman_id
        field.value = value
        
        if self.data_fields is None:
            self.data_fields = []
        self.data_fields.append(field)

    def get_field(self, type_id, airman_id=None, default_to_shared=True):
        default = None
        for field in self.data_fields:
            if field.type_id == type_id:
                if field.airman_id == airman_id:
                    return field
                elif default_to_shared and not field.airman_id:
                    default = field
        return default

    def get_field_value(self, type_id, airman_id=None, default_to_shared=True):
        field = self.get_field(type_id, airman_id, default_to_shared)
        return field.value if field else None

    def dump(self):
        def trim(value, max_len):
            if not value:
                return '-'
            value = str(value)
            return value[:max_len-3] + '...' if len(value) > max_len else value

        s = 'PARTICIPANTS\n'
        for participant in self.participants:
            person = Person.objects.get(unique_id=participant.airman_id)
            s += '  {0} {1}: {2}\n'.format(person.first_name, person.last_name, participant.role.name)

        s += 'DATA FIELDS\n'
        s += '{0:<35} | {1:<20} | '.format('', 'SHARED')
        for participant in self.participants:
            person = Person.objects.get(unique_id=participant.airman_id)
            s += '{0:<20} | '.format(person.first_name)
        s += '\n'

        field_types = LogEntryFieldTypeFactory.get_all()
        for field_type in field_types:
            s += '{0:<35} | '.format(field_type.display_name)

            value = self.get_field_value(field_type.id(), None)
            s += '{0:<20} | '.format(trim(value, 20))
            for participant in self.participants:
                value = self.get_field_value(field_type.id(), participant.airman_id, default_to_shared=False)
                s += '{0:<20} | '.format(trim(value, 20))
            s += '\n'

        return s



import datetime
import os


class _ColumnHandler(object):
	def __init__(self, column, field_name, header_names):
		self._field_name = field_name
		self._column = column
		header_name = self._column.header or field_name
		print('Importing column "{0}"...'.format(header_name))
		if header_name in header_names:
			self._index = header_names.index(header_name)
		else:
			if self._column.required:
				raise DataLoaderException('Column "{0}" not found.'.format(header_name), header_names)
			self._index = None

	def handle(self, loader, values):
		if self._index is None:
			setattr(loader, self._field_name, None)
		else:
			value = values[self._index]
			value = self._column.convert(value)
			setattr(loader, self._field_name, value)


class DataColumn(object):
	def __init__(self, header, required=True, preprocessor=None):
		self._header = header
		self._required = required
		self._preprocessor = preprocessor

	@property
	def header(self):
		return self._header

	@property
	def required(self):
		return self._required
	
	def get_handler(self, field_name, header_names):
		return _ColumnHandler(self, field_name, header_names)

	def convert(self, value):
		if self._preprocessor:
			value = self._preprocessor(value)
		return value


class StringColumn(DataColumn):
	pass


class BooleanColumn(DataColumn):
	_FALSE_VALUES = ['false', 'f', 'no', 'n', '0']

	def convert(self, value):
		value = super(BooleanColumn, self).convert(value)
		return value and value.lower() not in BooleanColumn._FALSE_VALUES


class IntColumn(DataColumn):
	def convert(self, value):
		value = super(IntColumn, self).convert(value)
		return int(value) if value else None


class FloatColumn(DataColumn):
	def convert(self, value):
		value = super(FloatColumn, self).convert(value)
		return float(value) if value else None


class DateTimeColumn(DataColumn):
	def __init__(self, header, fmt, required=True, preprocessor=None):
		super(DateTimeColumn, self).__init__(header=header, required=required, preprocessor=preprocessor)
		self._fmt = fmt

	def convert(self, value):
		value = super(DateTimeColumn, self).convert(value)
		return datetime.datetime.strptime(value, self._fmt) if value else None


class DateColumn(DateTimeColumn):
	def convert(self, value):
		value = super(DateColumn, self).convert(value)
		return value.date() if value else None


class TimeColumn(DateTimeColumn):
	def convert(self, value):
		value = super(TimeColumn, self).convert(value)
		return value.time() if value else None


class TimeDeltaColumn(DataColumn):
	def __init__(self, header, required=True, preprocessor=None):
		super(TimeDeltaColumn, self).__init__(header=header, required=required, preprocessor=preprocessor)


class EnumColumn(DataColumn):
	def __init__(self, header, enum_type, required=True, preprocessor=None):
		super(EnumColumn, self).__init__(header=header, required=required, preprocessor=preprocessor)
		self._enum_type = enum_type

	def convert(self, value):
		value = super(EnumColumn, self).convert(value)
		if value:
			if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
				return self._enum_type(int(value))
			else:
				return self._enum_type[value]
		else:
			return None


class CustomColumn(DataColumn):
	def __init__(self, header, loader, required=True, preprocessor=None):
		super(CustomColumn, self).__init__(header=header, required=required, preprocessor=preprocessor)
		self._loader = loader

	def convert(self, value):
		value = super(CustomColumn, self).convert(value)
		return self._loader(value)


class _ContainerHandler(object):
	def __init__(self, container, field_name, header_names):
		self._container = container
		self._field_name = field_name
		self._handlers = [v.get_handler(k, header_names) for k, v in container.definitions.iteritems()]

	def handle(self, loader, values):
		instance = self._container.model_type()
		setattr(loader, self._field_name, instance)
		for handler in self._handlers:
			handler.handle(instance, values)


class Container(DataColumn):
	def __init__(self, model_type, definitions):
		super(Container, self).__init__(header=None)
		self._model_type = model_type
		self._definitions = definitions

	@property
	def model_type(self):
		return self._model_type
	
	@property
	def definitions(self):
		return self._definitions
	
	def get_handler(self, field_name, header_names):
		return _ContainerHandler(self, field_name, header_names)


class DataLoader(object):

	def __init__(self, filename, delimiter=','):
		self._file = None
		self._filename = filename
		self._delimiter = delimiter
		self._header_names = []
		self._handlers = []
		self._line_number = 0
		self._total_error = 0
		self._total_size = os.path.getsize(self._filename)
		self._read_size = 0

	def __enter__(self):
		self._file = open(self._filename, 'r')
		self._load_header()
		return self

	def __exit__(self, exc_type, exc_value, exc_tb):
		self._file.close()
		print('Total error: {0}'.format(self._total_error))

	@property
	def line_number(self):
		return self._line_number

	@property
	def total_error(self):
		return self._total_error

	@property
	def progress(self):
		return float(self._read_size) / self._total_size if self._total_size > 0 else None

	def load(self, callback):
		while self.next():
			callback(self)

	def next(self):
		while True:
			self._values = self._load_values()
			if not self._values:
				return False

			try:
				for handler in self._handlers:
					handler.handle(self, self._values)
			except Exception as e:
				raise
				self._total_error += 1
				continue

			return True

	def has_data(self):
		return self._values is not None

	def to_dict(self):
		if self._values:
			return {name:self._values[i] for i, name in enumerate(self._header_names)}
		else:
			return None

	def _load_header(self):
		self._line_number += 1
		line = self._file.readline()
		self._read_size += len(line)

		line = line.lstrip('\xef\xbb\xbf').rstrip('\n')
		self._header_names = [x.strip('" ') for x in line.split(self._delimiter)]

		cls = type(self)
		field_names = [x for x in dir(cls) if isinstance(getattr(cls, x), DataColumn)]
		self._handlers = [getattr(cls, x).get_handler(x, self._header_names) for x in field_names]

	def _load_values(self):
		total_columns = len(self._header_names)
		row = self._load_row()
		while row:
			values = row.rstrip('\n').split(self._delimiter)
			if len(values) == total_columns:
				return [x.strip('" ') for x in values]
			elif len(values) < total_columns:
				next_row = self._load_row()
				if not next_row:
					self._total_error += 1
					return None
				row += next_row
			else:
				self._total_error += 1
				row = self._load_row()
		return None

	def _load_row(self):
		self._line_number += 1
		line = self._file.readline()
		if not line:
			return None

		self._read_size += len(line)
		return line


class DataLoaderException(Exception):
	pass




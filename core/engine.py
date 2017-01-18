from onelog.core import models
	

def register(cls):
	models.LogEntryFieldTypeFactory.register(cls)
	return cls

def require(cls_list, participant_role=None):
	def require_decorator(func):
		def func_wrapper(self, context):
			if not cls_list:
				return None
			if participant_role and (not context.current_participant or context.current_participant.role != participant_role):
				return None
			args = [context.get_field_value(x) for x in cls_list]
			if None in args:
				return None
			value = func(self, context, *args)
			return value
		return func_wrapper
	return require_decorator


class ComputeEngine(object):
	def __init__(self):
		self._field_types = models.LogEntryFieldTypeFactory.get_all()

	def compute(self, log_entry):
		self._compute_participant(log_entry, None)
		for participant in log_entry.participants:
			self._compute_participant(log_entry, participant)

	def _compute_participant(self, log_entry, participant):
		context = models.ComputeContext(log_entry, participant)
		airman_id = participant.airman_id if participant else None

		changed = True
		field_types = [x for x in self._field_types if not log_entry.get_field(type(x).id(), airman_id, default_to_shared=True)]
		while changed:
			changed = False
			unfilled_field_types = []
			for field_type in field_types:
				value = field_type.compute(context)
				if value is not None:
					# Save field value only if:
					#   1) field is shared, or
					#   2) value is different than value of shared field.
					if not participant or value != log_entry.get_field_value(type(field_type).id(), None):
						log_entry.add_field(type(field_type), value, airman_id)
						changed = True
				else:
					unfilled_field_types.append(field_type)
			field_types = unfilled_field_types

		


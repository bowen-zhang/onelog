import flask
import flask_restful
import json

from onelog.core import essential
from onelog.core import models


class LogEntry(flask_restful.Resource):
	def get(self):
		pipeline = [
		    {'$unwind': '$data_fields'},
		    {'$match': { 'data_fields.type_id': 5809168768645327672L}},
		    {'$sort': {'data_fields.raw_value': -1}},
		    {'$limit': 20},
		]

		results = list(models.LogEntry.objects.aggregate(*pipeline))
		ids = [x['_id'] for x in results]

		json = models.LogEntry.objects(pk__in=ids).to_json()
		return flask.Response(json, status=200, mimetype='application/json')

	def post(self):
		data = flask.request.get_json()
		log = models.LogEntry.objects.from_json(data)
		log.save()

	def put(self):
		data = flask.request.get_json()
		log = models.LogEntry.objects.from_json(data)
		log.update()

	def delete(self):
		data = flask.request.get_json()
		log = models.LogEntry.objects.from_json(data)
		log.delete()


class LogEntryCount(flask_restful.Resource):
	def get(self):
		return models.LogEntry.objects.count()


class LogEntryFieldType(flask_restful.Resource):
	def get(self):
		field_types = models.LogEntryFieldTypeFactory.get_all()
		field_types = [x.to_dict() for x in field_types]
		return flask.Response(json.dumps(field_types), status=200, mimetype='application/json')


class Aircraft(flask_restful.Resource):
	def get(self, tail_number):
		aircraft = models.Aircraft.objects.get(tail_number=tail_number)
		model = models.AircraftModel.objects.get(code=aircraft.aircraft_model_code)
		engine = models.EngineModel.objects.get(code=aircraft.engine_model_code)
		data = '{{ "aircraft": {0}, "model": {1}, "engine": {2} }}'.format(
			aircraft.to_json(), model.to_json(), engine.to_json())

		return flask.Response(data, status=200, mimetype='application/json')

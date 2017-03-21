import datetime
import json

import flask
import flask_restful
from webargs import fields
from webargs.flaskparser import use_kwargs

from onelog.core import essential
from onelog.core import models
from onelog.core import engine


class LogEntry(flask_restful.Resource):
    get_args = {
        'page': fields.Integer(required=False),
        'count_per_page': fields.Integer(required=False),
    }

    @use_kwargs(get_args)
    def get(self, page, count_per_page):
        page = page or -1
        count_per_page = count_per_page or 20

        total_entries = models.LogEntry.objects(type__=1).count()
        if total_entries == 0:
            return flask.Response('{}', status=200, mimetype='application/json')

        total_pages = (total_entries - 1) / count_per_page + 1
        if page < 0:
            page = total_pages + page + 1

        begin = (page - 1) * count_per_page
        end = page * count_per_page - 1
        json = models.LogEntry.objects(type__=1).order_by('timestamp')[begin:end].to_json()
        return flask.Response(json, status=200, mimetype='application/json')

    def post(self):
        data = flask.request.data
        log = models.LogEntry.from_json(data)
        log.timestamp = log.get_field_value(essential.TimeOut.id(), 4899861)
        log.created_at = datetime.datetime.utcnow()
        log.last_modified_at = log.created_at

        compute_engine = engine.ComputeEngine()
        compute_engine.compute(log)

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

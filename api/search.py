
import flask
import flask_restful
from webargs import fields
from webargs.flaskparser import use_kwargs


def register(cls):
    SearchEngine._questions.append(cls)
    return cls


class SearchEngine(flask_restful.Resource):
    get_args = {
        'query': fields.Str(required=True),
    }

    _questions = []

    @use_kwargs(get_args)
    def get(self, query):
        question = self._get_question(query)
        if not question:
            return flask.Response('', status=200, mimetype='application/json')
        
        answer = question.answer()
        if not answer:
            return flask.Response('', status=200, mimetype='application/json')

        return flask.Response(answer.to_json(), status=200, mimetype='application/json')

    def _get_question(self, query):
        query = query.lower().strip()
        for question_type in SearchEngine._questions:
            question = question_type.create_from(query)
            if question:
                return question

        return None

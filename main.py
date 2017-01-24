import flask
import flask_restful

from onelog.api import api
from onelog.api import search
from onelog.core import models

# To trigger registering
from onelog.api.answers import currency
from onelog.api.answers import statistic


app = flask.Flask(
  __name__,
  static_folder='web',
  template_folder='web')

flask_api = flask_restful.Api(app)
flask_api.add_resource(api.LogEntry, '/api/log_entry')
flask_api.add_resource(api.LogEntryCount, '/api/log_entry_count')
flask_api.add_resource(api.LogEntryFieldType, '/api/log_entry_field_type')
flask_api.add_resource(api.Aircraft, '/api/aircraft/<string:tail_number>')
flask_api.add_resource(search.SearchEngine, '/api/search')


@app.route("/logbook", methods=['GET'])
def index():
    return flask.render_template('logbook.html')

@app.route('/api/log-count')
def get_logs():
	logs = models.LogEntry.objects.all()
	print logs.count()
	return logs.to_json()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
import json

from onelog.core import models

pipeline = [
    {'$unwind': '$data_fields'},
    {'$match': { 'data_fields.type_id': 5809168768645327672L}},
    {'$sort': {'data_fields.raw_value': -1}},
    {'$limit': 20},
#    {'$lookup': { 'from': 'log_entry', 'localField': '_id', 'foreignField': '_id', 'as': 'entry'}},
#    {'$unwind': '$entry'},
#    {'$replaceRoot': { 'newRoot': '$entry'}},
]

results = list(models.LogEntry.objects.aggregate(*pipeline))
ids = [x['_id'] for x in results]

print models.LogEntry.objects(pk__in=ids).to_json()
#results = list(models.LogEntry.objects.aggregate(*pipeline))
#print json.dumps(results)

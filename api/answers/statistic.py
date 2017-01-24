import datetime

from onelog.api import search
from onelog.api.answers import common
from onelog.core import essential
from onelog.core import models


@common.question('total (time|hour|hours)')
@common.question('how many total (time|hour|hours)( do i have)?')
@search.register
class TotalTime(common.Question):

    def answer(self):
      pipeline = [
          {'$match': { 'type': models.LogEntryType.FLIGHT.value}},
          {'$unwind': '$data_fields'},
          {'$match': { 'data_fields.type_id': essential.TotalTime.id()}},
          {'$replaceRoot': { 'newRoot': '$data_fields'}},
      ]
      results = models.LogEntry.objects.aggregate(*pipeline)
      total_seconds = 0
      for result in results:
        total_seconds += float(result['raw_value'])

      return common.Answer(
        short_answer = '{0:.1f}h'.format(total_seconds/3600),
        full_answer = 'You have totally flown {0:.1f} hours.'.format(total_seconds/3600))

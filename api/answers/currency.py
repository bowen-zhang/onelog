import datetime

from onelog.api import search
from onelog.api.answers import common
from onelog.core import essential
from onelog.core import models


def _get_calendar_month(date):
    if date.month == 12:
        return datetime.datetime(date.year, date.month, 31)
    else:
        return datetime.datetime(date.year, date.month + 1, 1) - datetime.timedelta(days=1)

def _get_approach_due_date(log_entries):
    app_count = 0
    for log_entry in log_entries:
        airman_id = log_entry.participants[0].airman_id
        approaches = log_entry.get_field(essential.Approaches.id(), airman_id).value
        app_count += len(approaches)
        if app_count >=6:
            due = log_entry.timestamp + datetime.timedelta(days=180)
            return _get_calendar_month(due)

    return None

def _get_hold_due_date(log_entries):        
    for log_entry in log_entries:
        due = log_entry.timestamp + datetime.timedelta(days=180)
        return _get_calendar_month(due)

    return None

def _get_landing_due_date(log_entries):
    count = 0
    for log_entry in log_entries:
        airman_id = log_entry.participants[0].airman_id
        day_landings = log_entry.get_field_value(essential.DayLanding.id(), airman_id, default_value=0)
        night_landings = log_entry.get_field_value(essential.NightLanding.id(), airman_id, default_value=0)
        count += day_landings + night_landings
        if count >= 3:
            due = log_entry.timestamp + datetime.timedelta(days=90)
            return due

    return None

def _get_night_landing_due_date(log_entries):
    count = 0
    for log_entry in log_entries:
        airman_id = log_entry.participants[0].airman_id
        night_landings = log_entry.get_field_value(essential.NightLanding.id(), airman_id, default_value=0)
        count += night_landings
        if count >= 3:
            due = log_entry.timestamp + datetime.timedelta(days=90)
            return due

    return None

def _get_last_flight_review_date(log_entries):
    for log_entry in log_entries:
        return log_entry.timestamp
    return None

def _get_flight_review_due_date(log_entries):
    last = _get_last_flight_review_date(log_entries)
    if last:
        due = datetime.datetime(last.year + 2, last.month, 1)
        return _get_calendar_month(due)
    else:
        return None


@common.question('flight review')
@common.question('when was|is my last flight review')
@common.question('am i vfr current')
@common.question('vfr currency')
@common.question('what\'s my vfr currency')
@common.question('when does my vfr currency expire')
@common.answer('BFR', 'When is my next BFR due?')
@search.register
class FlightReviewDue(common.Question):

    def answer(self):
        flight_review = models.LogEntry.objects(data_fields__type_id=essential.FlightReview.id()).order_by('-timestamp').limit(1)
        due = _get_flight_review_due_date(flight_review)

        if not due:
            return common.Answer(short_answer = 'N/A')

        last = _get_last_flight_review_date(flight_review)
        if due < datetime.datetime.today():
            return common.Answer(
                short_answer = '<due>{0:%b %d, %Y}</due>'.format(due),
                full_answer = 'Your BFR is due since {0:%b %d, %Y}.'.format(due),
                details = 'Your last flight review was done on {0:%b %d, %Y}.'.format(last))
        else:
            return common.Answer(
                short_answer = '<current>{0:%b %d, %Y}</current>'.format(due),
                full_answer = 'Your next BFR is due by {0:%b %d, %Y}.'.format(due),
                details = 'Your last flight review was done on {0:%b %d, %Y}.'.format(last))


@common.question('can i take passengers')
@common.question('can i take passengers (at|during) (day time|daytime|day)')
@common.answer('Take Passengers', 'What\'s my currency for taking passengers?')
@search.register
class PassengerCurrencyDue(common.Question):

    def answer(self):
        landings = models.LogEntry.objects(data_fields__type_id__in=[essential.DayLanding.id(), essential.NightLanding.id()]).order_by('-timestamp').limit(3)
        due = _get_landing_due_date(landings)

        if not due:
            return common.Answer(short_answer = 'N/A')

        if due < datetime.datetime.today():
            return common.Answer(
                short_answer = '<due>{0:%b %d, %Y}</due>'.format(due),
                full_answer = 'You can NOT take passengers.')
        else:
            return common.Answer(
                short_answer = '<current>{0:%b %d, %Y}</current>'.format(due),
                full_answer = 'You can take passengers until {0:%b %d, %Y}.'.format(due),
                details = '<p>Your last few landings were:<br/>{0}</p>'.format(self._render_landings(landings)))

    def _render_landings(self, log_entries):
        html = '<ul>'

        count = 0
        for log_entry in log_entries:
            airman_id = log_entry.participants[0].airman_id
            day_landings = log_entry.get_field_value(essential.DayLanding.id(), airman_id, default_value=0)
            night_landings = log_entry.get_field_value(essential.NightLanding.id(), airman_id, default_value=0)

            html += '<li>{0:%b %d, %Y}: {1} Landings ({2} at Night)</li>'.format(log_entry.timestamp, day_landings + night_landings, night_landings)

            count += day_landings + night_landings
            if count >=3:
                break

        html += '</ul>'
        return html


@common.question('can i take passengers (at|during) (night|nighttime|night time)')
@common.answer('Take Passengers At Night', 'What\'s my currency for taking passengers at night?')
@search.register
class NightPassengerCurrencyDue(common.Question):

    def answer(self):
        night_landings = models.LogEntry.objects(data_fields__type_id=essential.NightLanding.id()).order_by('-timestamp').limit(3)
        due = _get_landing_due_date(night_landings)

        if not due:
            return common.Answer(short_answer = 'N/A')

        if due < datetime.datetime.today():
            return common.Answer(
                short_answer = '<due>{0:%b %d, %Y}</due>'.format(due),
                full_answer = 'You can NOT take passengers at night.')
        else:
            return common.Answer(
                short_answer = '<current>{0:%b %d, %Y}</current>'.format(due),
                full_answer = 'You can take passengers at night until {0:%b %d, %Y}.'.format(due),
                details = '<p>Your last few night landings were:<br/>{0}</p>'.format(self._render_landings(landings)))

    def _render_landings(self, log_entries):
        html = '<ul>'

        count = 0
        for log_entry in log_entries:
            airman_id = log_entry.participants[0].airman_id
            night_landings = log_entry.get_field_value(essential.NightLanding.id(), airman_id, default_value=0)

            html += '<li>{0:%b %d, %Y}: {1} night landings</li>'.format(log_entry.timestamp, night_landings)

            count += night_landings
            if count >=3:
                break

        html += '</ul>'
        return html


@common.question('am i ifr current')
@common.question('ifr currency')
@common.question('what\'s my ifr currency')
@common.question('when does my ifr currency expire')
@common.answer(short_title='IFR Currency', full_title='What\'s my IFR currency?')
@search.register
class IFRCurrencyDue(common.Question):

    def answer(self):
        recent_approaches = models.LogEntry.objects(data_fields__type_id=essential.Approaches.id()).order_by('-timestamp').limit(6)
        recent_holds = models.LogEntry.objects(data_fields__type_id=essential.Holds.id()).order_by('-timestamp').limit(1)

        due1 = _get_approach_due_date(recent_approaches)
        due2 = _get_hold_due_date(recent_holds)

        if not due1 and not due2:
            return common.Answer(
                short_answer = 'N/A',
                full_answer = '<warn>You are NOT IFR current.',
                details = 'You have not performed 6 approaches and holds so far.')
        if not due1:
            return common.Answer(
                short_answer = 'N/A',
                full_answer = '<warn>You are NOT IFR current.',
                details = 'You have not performed 6 approaches so far.')
        if not due2:
            return common.Answer(
                short_answer = 'N/A',
                full_answer = '<warn>You are NOT IFR current.',
                details = 'You have not performed holds so far.')

        due = min(due1, due2)
        if due < datetime.datetime.today():
            return common.Answer(
                short_answer = '<due>{0:%b %d, %Y}</due>'.format(due),
                full_answer = '<warn>You are NOT IFR current since {0:%b %d, %Y}.</warn>'.format(due),
                details = '')

        return common.Answer(
            short_answer = '<current>{0:%b %d, %Y}</current>'.format(due),
            full_answer = 'You are IFR current until {0:%b %d, %Y}.'.format(due),
            details = '<p>Your last few approaches were:<br/>{0}</p>'.format(
                self._render_approaches(recent_approaches)))

    def _render_approaches(self, log_entries):
        html = '<ul>'

        app_count = 0
        for log_entry in log_entries:
            airman_id = log_entry.participants[0].airman_id
            approaches = log_entry.get_field(essential.Approaches.id(), airman_id).value

            for approach in approaches:
                html += '<li>{0:%b %d, %Y}: {1} {2} RWY {3}</li>'.format(log_entry.timestamp, approach.airport, approach.approach_type, approach.runway)

            app_count += len(approaches)
            if app_count >=6:
                break

        html += '</ul>'
        return html


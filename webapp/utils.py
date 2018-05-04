# coding: utf-8

from flask import request, url_for, abort, jsonify
from flask import session as clienttoken
from werkzeug.routing import RequestRedirect, MethodNotAllowed, NotFound

from functools import wraps

from webapp import app
from webapp.config import DEBUG, RESPONSE_SCHEMA

import json

def build_response(result=None, error=None, result_schema=None, links=[]):
    '''Builds a HTTP response with the specified content in a JSON envelope'''
    resp_dict = dict()
    resp_dict['links'] = links
    if result is not None:
        resp_dict['result'] = result
    if result_schema:
        resp_dict['result-schema'] = result_schema
    if error:
        resp_dict['error'] = error
    # create response object
    resp = jsonify(resp_dict)
    # add content type, response schema
    resp.headers["Content-Type"] = 'application/vnd.backtoschool+json; schema="{}"'.format(
        request.url_root.rstrip('/') + url_for('schema', path=RESPONSE_SCHEMA))
    return resp


def build_link(endpoint, rel='http://relations.backtoschool.io/linkrelation', **kwargs):
    filename = endpoint.replace('_', '-') + '-schema.json'
    schema = request.url_root.rstrip('/') + url_for('schema', path=filename)
    res = [{'link': request.url_root.rstrip('/') + url_for(endpoint, **kwargs),
            'schema': schema,
            'rel': rel}]
    return res


def auth_check(f):
    '''Checks if the client is authorized to use the endpoint'''

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if DEBUG:
            return f(*args, **kwargs)

        # check if the endpoint is present in the authorized scopes
        if not clienttoken or 'scopes' not in clienttoken:
            # not yet authenticated
            abort(401)
        elif any(request.path.startswith(scope) for scope in clienttoken['scopes']):
            return f(*args, **kwargs)
        else:
            # not authorized for this endpoint
            abort(403)

    return decorated_function


def get_index(url):
    if url.startswith('/admin'):
        return 'admin', {}
    elif url.startswith('/teacher/'):
        try:
            teacher_id = int(url.split('/')[1])
            return 'teacher_with_id', {'teacher_id': teacher_id}
        except (ValueError, IndexError):
            return 'login', {}
    elif url.startswith('/parent'):
        try:
            parent_id = int(url.split('/')[1])
            return 'parent_with_id', {'parent_id': parent_id}
        except (ValueError, IndexError):
            return 'login', {}
    return 'login', {}


def get_endpoint_function(url, method):
    adapter = app.url_map.bind('localhost')
    try:
        return adapter.match(url, method=method)
    except RequestRedirect as e:
        # recursively match redirects
        return get_endpoint_function(e.new_url.split('localhost', maxsplit=1)[1], method)
    except (MethodNotAllowed, NotFound):
        # no match
        return '', {}


def check_appointment_time_constraint(date):
    return (date.minute == 30 or date.minute == 00) and (date.hour > 7 and date.hour < 13)


def available_slot_in_day(day_to_check, appointments, subjects):
    # Monday is 0 and Sunday is 6.

    if day_to_check.weekday() == 6:
        return False

    schedule = []
    for s in subjects:
        for t in json.loads(s.timetable):
            if t['day'] == day_to_check.weekday():
                schedule.append(t)

    app = [a for a in appointments if (
                a.date.year == day_to_check.year and a.date.month == day_to_check.month and a.date.day == day_to_check.day and a.teacher_accepted == 1)]

    if not schedule and not app:
        return True

    free = {8: [1, 1], 9: [1, 1], 10: [1, 1], 11: [1, 1], 12: [1, 1], 13: [1, 1]}

    for lesson in schedule:
        for x in range(lesson['start_hour'], lesson['end_hour'] + 1):
            # setto 2 slot come occupati -> lezioni vanno di ora in ora
            free[x][0] = 0
            free[x][1] = 0

    for a in app:
        if a.date.minute == 30:
            free[a.date.hour][1] = 0
        else:
            free[a.date.hour][0] = 0

    for x in free:
        if free[x][0] or free[x][1]:
            return True

    return False


def teacher_available(datetime_to_check, appointments, subjects):
    app = [a for a in appointments if (a.date == datetime_to_check and a.teacher_accepted == 1)]
    if not app:
        i = datetime_to_check.hour
        for s in subjects:
            schedule = json.loads(s.timetable)
            for t in schedule:
                if t['day'] == datetime_to_check.weekday():
                    if t['start_hour'] <= i and t['end_hour'] > i:
                        return False
    else:
        return False

    return True

# coding: utf-8

from flask import request, url_for, abort, jsonify
from flask import session as clienttoken
from werkzeug.routing import RequestRedirect, MethodNotAllowed, NotFound

from functools import wraps

from webapp import app
from webapp.config import DEBUG, RESPONSE_SCHEMA


def build_response(result=None, error=None, result_schema=None, links=[]):
    '''Builds a HTTP response with the specified content in a JSON envelope'''
    resp_dict = dict()
    resp_dict['links'] = links
    if result:
        resp_dict['result'] = result
    if result_schema:
        resp_dict['result-schema'] = result_schema
    if error:
        resp_dict['error'] = error
    # create response object
    resp = jsonify(resp_dict)
    # add content type, response schema
    resp.headers["Content-Type"] = 'application/vnd.highschool+json; schema="{}"'.format(
        request.url_root.rstrip('/') + url_for('schema', path=RESPONSE_SCHEMA))
    return resp


def build_link(endpoint, rel='http://relations.highschool.com/linkrelation', **kwargs):
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

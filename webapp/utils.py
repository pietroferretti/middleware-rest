# coding: utf-8

from flask import request, url_for, abort, jsonify
from flask import session as clienttoken
from werkzeug.routing import RequestRedirect, MethodNotAllowed, NotFound
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import json

from functools import wraps

from webapp import app
from webapp.config import DEBUG, RESPONSE_SCHEMA, SCHEMA_FOLDER


def schema_from_endpoint(endpoint):
    return endpoint.replace('_', '-') + '-schema.json'


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
    filename = schema_from_endpoint(endpoint)
    schema = request.url_root.rstrip('/') + url_for('schema', path=filename)
    res = [{'link': request.url_root.rstrip('/') + url_for(endpoint, **kwargs),
            'schema': schema,
            'rel': rel}]
    return res


def auth_check(f):
    '''Checks if the client is authorized to use the endpoint'''

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # avoid auth checks if debugging
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


def validate_schema(data, endpoint, method):
    '''Validate the JSON input according to the endpoint schema'''

    # get schema file from endpoint name
    filename = 'webapp/' + SCHEMA_FOLDER + '/' + schema_from_endpoint(endpoint)
    with open(filename) as f:
        # get schema for the specific method
        schema = json.load(f)
        actions = schema['actions']
        input_schema = None
        for obj in actions:
            if obj['method'] == method and 'inputschema' in obj:
                input_schema = obj['inputschema']
                break
        # validate input
        if input_schema is None:
            # no validation to be done
            return True
        try:
            validate(data, input_schema)
            # the validation was successful
            return True
        except ValidationError as e:
            if DEBUG:
                # print error to terminal
                print("* Failed validation on endpoint", endpoint)
                print(e.message)
            return False


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

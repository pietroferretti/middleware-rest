# coding: utf-8

from flask import request, redirect, url_for, send_from_directory
from flask import session as clienttoken

import hashlib
import datetime

from webapp import app
from webapp.config import DEBUG, SCHEMA_FOLDER
from webapp.utils import get_index, build_link, build_response
from webapp.db.db_declarative import session, Account


# default error handlers
@app.errorhandler(400)
def bad_request(e):
    # hypermedia back to endpoint, index
    links = [{'link': request.url, 'rel': 'self'}]
    index, kwargs = get_index(request.path)
    links += build_link(index, rel='http://relations.highschool.com/index', **kwargs)
    if DEBUG:
        return build_response(error=str(e), links=links), 400
    else:
        return build_response(error='Bad Request', links=links), 400


@app.errorhandler(401)
def authorization_required(e):
    # hypermedia to login
    links = build_link('login', rel='http://relations.highschool.com/login')
    if DEBUG:
        return build_response(error=str(e), links=links), 401
    else:
        return build_response(error='Authorization Required', links=links), 401


@app.errorhandler(403)
def forbidden(e):
    # hypermedia back to login
    links = build_link('login', rel='http://relations.highschool.com/login')
    if DEBUG:
        return build_response(error=str(e), links=links), 403
    else:
        return build_response(error='Forbidden', links=links), 403


@app.errorhandler(404)
def page_not_found(e):
    # hypermedia back to login
    links = build_link('login', rel='http://relations.highschool.com/login')
    if DEBUG:
        return build_response(error=str(e), links=links), 404
    else:
        return build_response(error='Page Not Found', links=links), 404


@app.errorhandler(405)
def method_not_allowed(e):
    # hypermedia back to endpoint, index
    links = [{'link': request.url, 'rel': 'self'}]
    index, kwargs = get_index(request.path)
    links += build_link(index, rel='http://relations.highschool.com/index', **kwargs)
    if DEBUG:
        return build_response(error=str(e), links=links), 405
    else:
        return build_response(error='Method Not Allowed', links=links), 405


@app.errorhandler(500)
def server_error(e):
    # hypermedia back to endpoint, index
    links = [{'link': request.url, 'rel': 'self'}]
    index, kwargs = get_index(request.path)
    links += build_link(index, rel='http://relations.highschool.com/index', **kwargs)
    if DEBUG:
        return build_response(error=str(e), links=links), 500
    else:
        return build_response(error='Internal Server Error', links=links), 500


@app.route('/')
def index():
    '''Root endpoint'''
    if DEBUG:
        return build_response('Hello world!')
    else:
        return redirect(url_for('login'))


@app.route('/schema/<path:path>')
def schema(path):
    '''Returns the schema with the given filename'''
    return send_from_directory(SCHEMA_FOLDER, path, mimetype='application/schema+json')


@app.route('/login/', methods=['POST'])
def login():
    '''Login endpoint'''

    # hypermedia
    links = build_link('login', rel='self')
    links += build_link('login', rel='http://relations.highschool.com/login')

    # check content type
    try:
        data = request.get_json()
    except TypeError:
        return build_response(error='The request was not valid JSON.', links=links), 400

    # check json content
    if 'username' not in data or 'password' not in data:
        return build_response(error='The JSON structure must contain all the requested parameters.', links=links), 400

    # get username, password
    username = data['username']
    user_password = data['password']

    # check if the account exists in the database
    account = session.query(Account).filter_by(username=username).one()
    if not account:
        return build_response(error='Incorrect username or password.', links=links), 400

    salt, hash = account.password.split(':')
    salt = bytes.fromhex(salt)
    hash = bytes.fromhex(hash)
    user_hash = hashlib.pbkdf2_hmac('sha256', user_password.encode(), salt, 100000)
    if not user_hash == hash:
        return build_response(error='Incorrect username or password', links=links), 400

    # check if admin, teacher or parent
    # assign different scopes in each case
    role = account.type
    if role == 'admin':
        scopes = ['/admin/', '/teacher/', '/parent/']
        links += build_link('admin', rel='http://relations.highschool.com/index')
    elif role == 'teacher':
        teacher_id = account.teacher_id
        scopes = ['/teacher/{}/'.format(teacher_id)]
        links += build_link('teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/index')
    elif role == 'parent':
        parent_id = account.parent_id
        scopes = ['/parent/{}/'.format(parent_id)]
        links += build_link('parent_with_id', parent_id=parent_id,
                            rel='http://relations.highschool.com/index')
    else:
        raise ValueError('Role "{}" not recognized!'.format(role))

    # save authorized endpoints in a cryptographically secure client side cookie
    clienttoken['scopes'] = scopes
    clienttoken.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(hours=1)

    return build_response({'message': 'Login successful.', 'username': data['username']}, links=links)

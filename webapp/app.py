#!/usr/bin/env/python3
# coding: utf-8

# from teacher import *
# from parent import *
# from admin import *

# import json

# TODO
# definire tutte le funzioni per ogni endpoint
# spostare funzioni in altri file?
# che tipo per gli id? dipende da database schema
# aggiungere PUT dove ci sono POST?
# aggiungere metodi DELETE dove servono (es notification)
# aggiungere subject ai grade

from flask import Flask, request, jsonify, abort, url_for, send_from_directory
from flask import session as clienttoken
from functools import wraps
from db.db_declarative import *
from datetime import datetime, timedelta
from sqlalchemy.orm.exc import NoResultFound

import os
import hashlib

import IPython

DEBUG = True
RESPONSE_SCHEMA = 'response-schema.json'

app = Flask(__name__)
app.secret_key = '\x8d)2m_\xa4\x8e\xe1\xaa\x8ca\xbd\xc6\xed@\xcbxw~\xe8x\xa2\xa2^'

def build_response(result=None, error=None, result_schema=None, links=[]):
    '''Builds a HTTP response with the specified content in a JSON envelope'''
    resp_dict = {}
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
    # TODO get schema for endpoint
    return [{'link': request.url_root.rstrip('/') + url_for(endpoint, **kwargs), 
            'rel': rel}]


def check_appointment_time_constraint(date):
    return (date.minute == 30 or date.minute == 00) and (date.hour > 7 and date.hour < 13)

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


# default error handlers
@app.errorhandler(400)
def bad_request(e):
    # hypermedia back to endpoint, index
    links = [{'link': request.url, 'rel': 'self'}]
    index, kwargs = get_index(request.path)
    links += build_link(index, **kwargs, rel='http://www.highschool.com/index')
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
    links += build_link(index, **kwargs, rel='http://www.highschool.com/index')
    if DEBUG:
        return build_response(error=str(e), links=links), 405
    else:
        return build_response(error='Method Not Allowed', links=links), 405


@app.errorhandler(500)
def server_error(e):
    # hypermedia back to endpoint, index
    links = [{'link': request.url, 'rel': 'self'}]
    index, kwargs = get_index(request.path)
    links += build_link(index, **kwargs, rel='http://www.highschool.com/index')
    if DEBUG:
        return build_response(error=str(e), links=links), 500
    else:
        return build_response(error='Internal Server Error', links=links), 500


def auth_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if DEBUG == True:
            return f(*args, **kwargs)

        # check if the endpoint is present in the authorized scopes
        if not clienttoken or 'scopes' not in clienttoken:
            # not yet authenticated
            abort(401)
        elif any(path.startswith(scope) for scope in clienttoken['scopes']):
            return f(*args, **kwargs)
        else:
            # not authorized for this endpoint
            abort(403)
    return decorated_function



@app.route('/')
def index():
    '''Root endpoint'''
    # TODO redirect to /login
    d = "Hello World"
    # IPython.embed()
    return build_response(d)


@app.route('/schema/<path:path>')
def schema(path):
    '''Returns the schema with the given filename'''
    return send_from_directory('schemas', path, mimetype='application/schema+json')


@app.route('/login/', methods=['POST'])
def login():
    # TODO hypermedia

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
    app.permanent_session_lifetime = timedelta(hours=1)

    return build_response({'message': 'Login successful.', 'username': data['username']}, links=links)


'''TEACHER'''

@app.route('/teacher/<int:teacher_id>/')
@auth_check
def teacher_with_id(teacher_id):
    """teacher main index: show teacher info, hypermedia"""
    # get teacher with id
    teacher = session.query(Teacher).get(teacher_id)
    # check if the teacher was found
    if not teacher:
        # TODO check race condition and revoke cookie
        links = build_link('login', rel='http://relations.highschool.com/login')
        return build_response(None, error='Teacher id not found.', login=login), 404
    # return response
    res = {'name': teacher.name, 
           'lastname': teacher.lastname}

    # hypermedia links
    #links = [{'link': request.url_root.rstrip('/') + url_for('teacher_with_id', teacher_id=teacher_id)}]
    links = build_link('teacher_data', teacher_id=teacher_id,
                       rel='http://relations.highschool.com/data')
    links += build_link('teacher_data', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/updatedata')
    links += build_link('teacher_class', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/classlist')
    links += build_link('teacher_timetable', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/timetable')
    links += build_link('teacher_notifications', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/notificationlist')
    links += build_link('teacher_appointment', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='self')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/data/', methods=['GET', 'PUT'])
@auth_check
def teacher_data(teacher_id):
    # hypermedia
    links = build_link('teacher_data', teacher_id=teacher_id, 
                   rel='http://relations.highschool.com/data')
    links += build_link('teacher_data', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/updatedata')
    links += build_link('teacher_data', teacher_id=teacher_id,
                        rel='self')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')

    if request.method == 'PUT':
        '''modify personal data'''

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.', links=links), 400

        # check json content
        if 'name' not in data and 'lastname' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.', links=links), 400

        # session
        if 'name' in data:
            newname = data['name']

        newname = data['name']
        newlastname = data['lastname']
        teacher = session.query(Teacher).get(teacher_id)
        if 'name' in data:
            teacher.name = data['name']
        if 'lastname' in data:
            teacher.lastname = data['lastname']
        session.commit()

        return build_response({'message':'Update successful.'}, links=links)
        # TODO ha senso 'message'?
    else:
        '''show personal data'''
        # get data from teachers with id
        teacher = session.query(Teacher).get(teacher_id)
        # check if the teacher was found
        if not teacher:
            return build_response(None, error='Teacher id not found.'), 404

        res = {'name': teacher.name, 
               'lastname': teacher.lastname}

        # hypermedia
        links = build_link('teacher_data', teacher_id=teacher_id, 
                           rel='http://relations.highschool.com/data')
        links += build_link('teacher_data', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/updatedata')
        links += build_link('teacher_data', teacher_id=teacher_id,
                            rel='self')
        links += build_link('teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/index')

        return build_response(res, links=links)

@app.route('/teacher/<int:teacher_id>/class/')
@auth_check
def teacher_class(teacher_id):
    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id, 
                       rel='http://relations.highschool.com/index')
    links += build_link('teacher_class', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/classlist')
    links += build_link('teacher_class', teacher_id=teacher_id,
                        rel='self')

    '''show list of classes for the specific teacher'''
    teacher = session.query(Teacher).get(teacher_id)
    # check if the teacher was found
    if not teacher:
        links = build_link('login', rel='http://relations.highschool.com/login')
        return build_response(None, error='Teacher id not found.', links=links), 404
    # return response
    classes = teacher.classes
    cl = []

    for c in classes:
        cl.append({'id': c.id, 'name': c.name, 'room': c.room})

    res = {'class': cl}

    # more hypermedia
    for i in range(min(10, len(cl))):
        links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=cl[i]['id'],
                            rel='http://relations.highschool.com/class')

    return build_response(res, links=links)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/')
@auth_check
def teacher_class_with_id(teacher_id, class_id):
    '''show class info for that teacher (students, subjects, timetable)'''

    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_class', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/classlist')
    links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/class')
    links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=class_id,
                        rel='self')
    links += build_link('teacher_class_timetable', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/timetable')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/subjectlist')

    c = session.query(Class).get(class_id)
    subjects_list = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).all()

    if not c:
        links = build_link('teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/index')
        links += build_link('teacher_class', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/classlist')
        return build_response(None, error='Class id not found.', links=links), 404

    students = c.students
    st = []
    for s in students:
        st.append({'id': s.id, 'name': s.name, 'lastname': s.lastname})

    subjects = []
    for s in subjects_list:
        subjects.append({'id': s.id, 'name': s.name})

    res = {'class': {'id': class_id, 'name': c.name, 'room': c.room, 'students': st, 'subjects': subjects}}

    return build_response(res, links=links)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/')
@auth_check
def teacher_subject(teacher_id, class_id):
    '''show list of subject taught by a teacher in a class'''

    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_class', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/class')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/subjectlist')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='self')

    subjects_list = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).all()

    if not subjects_list:
        links = build_link('teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/index')
        return build_response(None, error='Subjects not found.', links=links), 404

    subjects = []
    for s in subjects_list:
        subjects.append({'id': s.id, 'name': s.name})

    res = {'subjects': subjects}

    # more hypermedia
    for i in range(min(10, len(subjects))):
        links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subjects[i]['id'],
                            rel='http://relations.highschool.com/subject')

    return build_response(res, links=links)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/')
@auth_check
def teacher_subject_with_id(teacher_id, class_id, subject_id):
    '''show subject info taught by a teacher'''

    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/subjectlist')
    links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/subject')
    links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='self')
    links += build_link('teacher_student', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/studentlist')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/grades')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/publishgrades')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/updategrades')

    subject = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).filter_by(
        id=subject_id).first()
    if not subject:
        links = build_link('teacher_with_id', teacher_id=teacher_id,
                           rel='http://relations.highschool.com/index')
        return build_response(None, error='Subject not found.', links=links), 404

    res = {'id': subject.id, 'name': subject.name}

    return build_response(res, links=links)


# MA È UGUALE A CLASS DI TEACHER?
@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/')
@auth_check
def teacher_student(teacher_id, class_id, subject_id):
    '''show list of students for a subject taught by a teacher'''

    links = build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/subject')
    links += build_link('teacher_student', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/studentlist')
    links += build_link('teacher_student', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='self')

    c = session.query(Class).get(class_id)
    subject = session.query(Subject).filter_by(id=subject_id).filter_by(teacher_id=teacher_id).filter_by(
        class_id=class_id).first()

    if not c:
        links = build_link('teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/index')
        links += build_link('teacher_class', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/classlist')
        return build_response(None, error='Class id not found.', links=links), 404

    if not subject:
        links = build_link('teacher_with_id', teacher_id=teacher_id,
                           rel='http://relations.highschool.com/index')
        links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                            rel='http://relations.highschool.com/subjectlist')
        return build_response(None, error='Subject id not found.', links=links), 404

    students = c.students
    st = []
    for s in students:
        st.append({'id': s.id, 'name': s.name, 'lastname': s.lastname})

    # subjects = []
    # for s in subjects_list:
    #     subjects.append({'id': s.id, 'name': s.name})

    res = {'students': st}

    # more hypermedia
    for i in range(min(10, len(st))):
        links += build_link('teacher_student_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            student_id=st[i]['id'], rel='http://relations.highschool.com/student')

    return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/<int:student_id>/')
@auth_check
def teacher_student_with_id(teacher_id, class_id, student_id):
    # TODO
    pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/<int:student_id>/grade/', methods=['GET', 'POST', 'PUT'])
@auth_check
def teacher_student_grades(teacher_id, class_id, subject_id, student_id):
    if request.method == 'POST':
        '''add new grade'''
        # TODO student in class?
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'date' not in data or 'value' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400

        date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
        value = data['value']

        new_grade = Grade(date=date, subject_id=subject_id, student_id=student_id, value=value)

        session.add(new_grade)
        session.commit()
        # return confirmation, new id
        new_id = new_grade.id
        return build_response({'id': new_id}), 201

    elif request.method == 'PUT':
        '''edit old grade'''
        # FIXME aggiungere un /grade/<grade_id> ?
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'id' not in data:
            return build_response(None, error='The JSON structure must contain the grade id.'), 400

        grade = session.query(Grade).filter_by(id=int(data['id'])).filter_by(subject_id=subject_id).filter_by(
            student_id=student_id).first()

        if not grade:
            return build_response(None, error='Grade not found.'), 404

        if 'date' in data:
            grade.date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

        if 'value' in data:
            grade.value = int(data['value'])

        session.commit()
        return build_response({'message': 'Update successful.'})
        # TODO ha senso 'message'?

    else:
        '''show grades list'''
        grade_list = session.query(Grade).filter_by(subject_id=subject_id).filter_by(student_id=student_id).all()

        if not grade_list:
            return build_response(None, error='Grade not found.'), 404

        check_teacher_class_subj = session.query(Subject).filter_by(class_id=class_id).filter_by(
            teacher_id=teacher_id).filter_by(id=subject_id).first()

        if not check_teacher_class_subj:
            return build_response(None, error='Data not found.'), 404

        grades = []
        for g in grade_list:
            grades.append({'id': g.id, 'date': g.date, 'value': g.value})

        res = {'grades': grades}

        return build_response(res)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/grade/', methods=['GET', 'POST'])
@auth_check
def teacher_class_grades(teacher_id, class_id, subject_id):
    check_teacher_class_subj = session.query(Subject).filter_by(class_id=class_id).filter_by(
        teacher_id=teacher_id).filter_by(id=subject_id).one()

    if not check_teacher_class_subj:
        return build_response(None, error='Data not found.'), 404

    if request.method == 'POST':
        '''add new list of grades for the whole class'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        # if 'date' not in data or 'value' not in data:
        #     return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400

        for grade in data['grades']:
            date = datetime.strptime(grade['date'], '%Y-%m-%d %H:%M')
            value = grade['value']
            student_id = grade['student_id']

            try:
                check_student_class = session.query(Student).filter_by(id=student_id).filter_by(class_id=class_id).one()
            except NoResultFound:
                session.rollback()
                return build_response(grade, error='Student not in this class.'), 404

            new_grade = Grade(date=date, subject_id=subject_id, student_id=student_id, value=value)
            session.add(new_grade)
        session.commit()

        # # return confirmation, new id
        # new_id = new_grade.id
        return build_response({'id': 'ok'}), 201

    else:
        '''show grades for the whole class for that subject'''
        student_list = session.query(Student).filter_by(class_id=class_id).all()

        if not student_list:
            return build_response(None, error='Students not found.'), 404

        st = []
        for s in student_list:
            grades_list = []
            for g in s.grades:
                grades_list.append({'grade': {'id': g.id, 'date': g.date, 'value': g.value}})
            st.append({'student': {'id': s.id, 'name': s.name, 'lastname': s.lastname, 'grades': grades_list}})

        res = {'students': st}

        return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/timetable/')
@auth_check
def teacher_class_timetable(teacher_id, class_id):
    '''show timetable for that class'''
    # FIXME serve? informazioni complete vengono date da /class/
    pass

@app.route('/teacher/<int:teacher_id>/timetable/')
@auth_check
def teacher_timetable(teacher_id):
    '''show complete timetable for a teacher'''
    pass



# fixme cambiare risultati appointment
@app.route('/teacher/<int:teacher_id>/appointment/', methods=['GET', 'POST'])
@auth_check
def teacher_appointment(teacher_id):
    if request.method == 'POST':
        '''create new appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'date' not in data or 'parent_id' not in data or 'room' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        new_date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

        if (check_appointment_time_constraint(new_date)):
            new_appointment = Appointment(date=new_date, teacher_accepted=1, parent_accepted=0, teacher_id=teacher_id,
                                          room=data['room'], parent_id=data['parent_id'])
            session.add(new_appointment)
            session.commit()
            new_id = new_appointment.id
            return build_response({'id': new_id}), 201

        else:
            return build_response(None, error='Wrong date/time.'), 400

    '''show list of appointments for a teacher'''

    appointments_list = session.query(Appointment).filter_by(teacher_id=teacher_id).all()

    if not appointments_list:
        return build_response(None, error='Appointments not found.'), 404

    appointments = []
    for a in appointments_list:
        parent = session.query(Parent).filter_by(id=a.parent_id).one()
        appointments.append({'appointment': {'id': a.id, 'date': a.date, 'room': a.room,
                                             'parent_accepted': a.parent_accepted,
                                             'teacher_accepted': a.teacher_accepted,
                                             'parent': {'name': parent.name, 'lastname': parent.lastname}}})

    return build_response(appointments)


@app.route('/teacher/<int:teacher_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
@auth_check
def teacher_appointment_with_id(teacher_id, appointment_id):

    appointment = session.query(Appointment).filter_by(id=appointment_id).filter_by(teacher_id=teacher_id).one()

    if not appointment:
        return build_response(None, error='Appointment not found.'), 404

    if request.method == 'PUT':
        '''edit appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'date' in data:
            new_date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

            if (check_appointment_time_constraint(new_date)):
                appointment.date = new_date
                appointment.parent_accepted = 0
            else:
                return build_response(None, error='Wrong date/time.'), 400


        if 'room' in data:
            appointment.room = data['room']

        if 'parent_id' in data:
            if int(data['parent_id']) != appointment.parent_id:
                appointment.parent_accepted = 0
            appointment.parent_id = int(data['parent_id'])


        if 'teacher_accepted' in data:
            appointment.teacher_accepted = int(data['teacher_accepted'])

        session.commit()
        return build_response({'message': 'Update successful.'})
        
    else:
        '''show appointment info'''
        parent = session.query(Parent).filter_by(id=appointment.parent_id).one()

        return build_response({'appointment': {'date': appointment.date, 'room': appointment.room,
                                               'teacher_accepted': appointment.teacher_accepted,
                                               'parent_accepted': appointment.parent_accepted,
                                               'parent': {'id': parent.id, 'name': parent.name,
                                                          'lastname': parent.lastname}}})

@app.route('/teacher/<int:teacher_id>/notifications/')
@auth_check
def teacher_notifications(teacher_id):
    '''show notifications for this teacher'''
    teacher = session.query(Teacher).filter_by(id=teacher_id).one()

    if not teacher:
        return build_response(None, error='Teacher not found.')

    notifications = []
    for n in teacher.notifications:
        notifications.append({'notification': {'id': n.id, 'date': n.date, 'text': n.text}})

    return build_response(notifications)

'''PARENT'''

@app.route('/parent/<int:parent_id>/')
@auth_check
def parent_with_id(parent_id):
    '''parent main index: parent info, hypermedia'''

    parent = session.query(Parent).filter_by(id=parent_id).first()

    if not parent:
        return build_response(None, error='Parent id not found'), 404
    res = {'name': parent.name,
           'lastname': parent.lastname}
    return build_response(res)


@app.route('/parent/<int:parent_id>/data/', methods=['GET', 'PUT'])
@auth_check
def parent_data(parent_id):
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, error='Parent not found.'), 404

    if request.method == 'PUT':
        '''edit parent personal data'''

        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'name' in data:
            parent.name = data['name']

        if 'lastname' in data:
            parent.lastname = data['lastname']

        session.commit()
        return build_response({'message': 'Update successful.'})

    else:
        '''show parent personal data'''

        return build_response({'data': {'name': parent.name, 'lastname': parent.lastname, 'id': parent.id}})

@app.route('/parent/<int:parent_id>/child/')
@auth_check
def parent_child(parent_id):
    '''list children of parent'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    if not parent.children:
        return build_response(None, 'Student not found.')

    children = []
    for c in parent.children:
        children.append({'student': {'name': c.name, 'lastname': c.lastname, 'id': c.id}})

    return build_response(children)


@app.route('/parent/<int:parent_id>/child/<int:student_id>/')
@auth_check
def parent_child_with_id(parent_id, student_id):
    '''show info of student'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    student = session.query(Student).filter_by(parent_id=parent_id).filter_by(id=student_id).one()

    if not student:
        return build_response(None, 'Student not found.')

    c = session.query(Class).filter_by(id=student.class_id).first()

    # if not c:
    #     res = 'Not enrolled.'
    # else:
    # ASSUMPTION: every student has a class associated
    subjects = []
    for s in c.subjects:
        subjects.append({'id': s.id, 'name': s.name})

    res = {'id': c.id, 'name': c.name, 'room': c.room, 'subjects': subjects}

    return build_response(
        {'student': {'name': student.name, 'lastname': student.lastname, 'id': student.id, 'class': res}})
    

@app.route('/parent/<int:parent_id>/child/<int:student_id>/data/', methods=['GET', 'PUT'])
@auth_check
def parent_child_data(parent_id, student_id):
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    student = session.query(Student).filter_by(parent_id=parent_id).filter_by(id=student_id).one()

    if not student:
        return build_response(None, 'Student not found.')

    if request.method == 'PUT':
        '''edit child personal data'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'name' in data:
            student.name = data['name']

        if 'lastname' in data:
            student.lastname = data['lastname']

        session.commit()

        return build_response({'message': 'Update successful.'})

    else:
        '''show child personal data'''
        return build_response({'data': {'name': student.name, 'lastname': student.lastname, 'id': student.id}})

@app.route('/parent/<int:parent_id>/child/<int:student_id>/grades/')
@auth_check
def parent_child_grades(parent_id, student_id):
    '''show all grades of the student'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    student = session.query(Student).filter_by(parent_id=parent_id).filter_by(id=student_id).one()

    if not student:
        return build_response(None, 'Student not found.')

    grades = []
    for g in student.grades:
        grades.append({'grade': {'id': g.id, 'date': g.date, 'value': g.value}})

    return build_response({'grades': grades})

@app.route('/parent/<int:parent_id>/child/<int:student_id>/teachers/')
@auth_check
def parent_child_teacher(parent_id, student_id):
    '''list all child's teachers'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    student = session.query(Student).filter_by(parent_id=parent_id).filter_by(id=student_id).one()

    if not student:
        return build_response(None, 'Student not found.')

    c = session.query(Class).filter_by(id=student.class_id).first()

    if not c:
        res = 'Not enrolled.'


# todo capire come vogliamo gestire gli errori, esempio id che non esiste del teacher
@app.route('/parent/<int:parent_id>/appointment/', methods=['GET', 'POST'])
@auth_check
def parent_appointment(parent_id):
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    if request.method == 'POST':
        '''create new appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'date' not in data or 'teacher_id' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        new_date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

        if (check_appointment_time_constraint(new_date)):
            new_appointment = Appointment(date=new_date, teacher_accepted=0, parent_accepted=1,
                                          teacher_id=data['teacher_id'], parent_id=parent_id)
            session.add(new_appointment)
            session.commit()
            new_id = new_appointment.id
            return build_response({'id': new_id}), 201

        else:
            return build_response(None, error='Wrong date/time.'), 400


    else:
        '''show all appointments'''
        appointments = []
        for a in parent.appointments:
            teacher = session.query(Teacher).filter_by(id=a.teacher_id).one()
            appointments.append({'id': a.id, 'date': a.date, 'room': a.room, 'teacher accepted': a.teacher_accepted,
                                 'parent_accepted': a.parent_accepted,
                                 'teacher': {'id': a.teacher_id, 'name': teacher.name, 'lastname': teacher.lastname}})

        return build_response(appointments)

# TODO calendar-like support

@app.route('/parent/<int:parent_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
@auth_check
def parent_appointment_with_id(parent_id, appointment_id):
    appointment = session.query(Appointment).filter_by(id=appointment_id).filter_by(parent_id=parent_id).one()

    if not appointment:
        return build_response(None, 'Appointment not found.')


    if request.method == 'PUT':
        '''edit appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'date' in data:
            new_date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

            if (check_appointment_time_constraint(new_date)):
                appointment.date = new_date
                appointment.parent_accepted = 0
            else:
                return build_response(None, error='Wrong date/time.'), 400

        if 'teacher_id' in data:
            if int(data['teacher_id']) != appointment.teacher_id:
                appointment.teacher_accepted = 0
            appointment.teacher_id = int(data['teacher_id'])

        if 'parent_accepted' in data:
            appointment.parent_accepted = int(data['parent_accepted'])

        session.commit()

        return build_response({'message': 'Update successful.'})
    else:
        '''show appointment info'''
        teacher = session.query(Teacher).filter_by(id=appointment.teacher_id).one()

        return build_response({'appointment': {'date': appointment.date, 'room': appointment.room,
                                               'teacher_accepted': appointment.teacher_accepted,
                                               'parent_accepted': appointment.parent_accepted,
                                               'teacher': {'name': teacher.name, 'lastname': teacher.lastname}}})


@app.route('/parent/<int:parent_id>/appointment/teacher/<int:teacher_id>/year/<int:year>/month/<int:month>/')
@auth_check
def parent_appointment_month(parent_id, teacher_id, year, month):
    '''Show which days have appointments and free slots for the month'''
    pass


@app.route(
    '/parent/<int:parent_id>/appointment/teacher/<int:teacher_id>/year/<int:year>/month/<int:month>/day/<int:day>/')
@auth_check
def parent_appointment_day(parent_id, teacher_id, year, month, day):
    '''Show appointments, free slots for the day'''
    pass


@app.route('/parent/<int:parent_id>/payment/')
@auth_check
def parent_payment(parent_id):
    '''list all payments, paid or pending'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    payments = []

    for p in parent.payments:
        payments.append({'id': p.id, 'amount': p.amount, 'date': p.date, 'reason': p.reason, 'pending': p.is_pending})

    return build_response({'payments': payments})
    

@app.route('/parent/<int:parent_id>/payment/paid/')
@auth_check
def parent_payment_paid(parent_id):
    '''list old paid payments'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    payments = []

    for p in parent.payments:
        if (not p.is_pending):
            payments.append({'id': p.id, 'amount': p.amount, 'date': p.date, 'reason': p.reason})

    return build_response({'payments': payments})

@app.route('/parent/<int:parent_id>/payment/pending/')
@auth_check
def parent_payment_pending(parent_id):
    '''list pending payments'''
    parent = session.query(Parent).filter_by(id=parent_id).one()

    if not parent:
        return build_response(None, 'Parent not found.')

    payments = []

    for p in parent.payments:
        if (p.is_pending):
            payments.append({'id': p.id, 'amount': p.amount, 'date': p.date, 'reason': p.reason})

    return build_response({'payments': payments})

@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/')
@auth_check
def parent_payment_with_id(parent_id, payment_id):
    '''show payment info'''
    payment = session.query(Payment).filter_by(id=payment_id).one()

    if not payment:
        return build_response(None, 'Payment not found.')

    if (payment.parent_id != parent_id):
        return build_response(None, 'Data not found.')

    return build_response({'payment': {'id': payment.id, 'amount': payment.amount, 'date': payment.date,
                                       'reason': payment.reason, 'pending': payment.is_pending}})

@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/pay/', methods=['POST'])
@auth_check
def parent_pay(parent_id, payment_id):
    '''magic payment endpoint'''
    pass

@app.route('/parent/<int:parent_id>/notifications/')
@auth_check
def parent_notifications(parent_id):
    '''show notifications for this parent'''
    # notifications = session.query(Notification).filter_by(parent_id=parent_id).all()

    # if not notifications:
    #     return build_response(None, 'Data not found.')

    # notifications_list = []
    # for n in notifications
    pass


'''ADMIN STUFF'''

@app.route('/admin/', methods=['GET', 'POST'])
@auth_check
def admin():
    if request.method == 'POST':
        '''Create new admin account'''

        # hypermedia
        links = build_link('admin', rel='self')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        links += build_link('admin', rel='http://relations.highschool.com/createadmin')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.'), 400

        # check json content
        if 'username' not in data or 'password' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        existing = session.query(Account).filter_by(username=data['username']).all()
        if existing:
            return build_response(error='The username is already in use.', links=links), 400

        # create account object
        salt = os.urandom(16)
        hash = hashlib.pbkdf2_hmac('sha256', data['password'].encode(), salt.encode(), 100000)
        saved_password = salt.hex() + ':' + hash.hex()
        account = Account(username=data['username'], password=saved_password, type='admin')

        # insert account in database
        session.add(account)
        session.commit()

        # build response object
        a_obj = {'username': data['username'], 'role': 'admin'}
        res = {'account': a_obj}

        return build_response(res, links=links), 201

    else:
        '''Admin index'''

        # hypermedia
        links = build_link('admin', rel='self')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        links += build_link('admin', rel='http://relations.highschool.com/createadmin')
        links += build_link('admin_teacher', rel='http://relations.highschool.com/teacherlist')
        links += build_link('admin_teacher', rel='http://relations.highschool.com/createteacher')
        links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
        links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
        links += build_link('classes', rel='http://relations.highschool.com/classlist')
        links += build_link('student', rel='http://relations.highschool.com/studentlist')
        links += build_link('student', rel='http://relations.highschool.com/createstudent')
        links += build_link('payment', rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment', rel='http://relations.highschool.com/createpayment')
        links += build_link('notification', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification', rel='http://relations.highschool.com/createnotification')

        build_response(links=links)


@app.route('/admin/teacher/', methods=['GET', 'POST'])
@auth_check
def admin_teacher():
    if request.method == 'POST':
        '''Create a new teacher account'''

        # hypermedia
        links = build_link('admin_teacher', rel='self')
        links += build_link('admin_teacher', rel='http://relations.highschool.com/teacherlist')
        links += build_link('admin_teacher', rel='http://relations.highschool.com/createteacher')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check json content
        if 'name' not in data or 'lastname' not in data or 'username' not in data or 'password' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        existing = session.query(Account).filter_by(username=data['username'])
        if existing:
            return build_response(error='The username is already in use.', links=links), 400

        # create new teacher object
        name = data['name']
        lastname = data['lastname']
        new_teacher = Teacher(name=name, lastname=lastname)

        # insert new teacher in db
        session.add(new_teacher)
        session.commit()

        # create new account object
        username = data['username']
        password = data['password']
        salt = os.urandom(16)
        hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        saved_password = salt.hex() + ':' + hash.hex()
        account = Account(username=username, password=saved_password, type='teacher', teacher_id=new_teacher.id)

        # add to database
        session.add(account)
        session.commit()

        # return teacher, account objects
        t_obj = {'id': new_teacher.id, 'name': name, 'lastname': lastname}
        a_obj = {'username': username, 'role': 'teacher', 'teacher_id': new_teacher.id}
        res = {'teacher': t_obj, 'account': a_obj}

        # more hypermedia
        links += build_link('admin_teacher_with_id', teacher_id=new_id, rel='http://relations.highschool.com/teacher')

        return build_response(res, links=links), 201

    else:
        '''List of teachers'''

        # hypermedia
        links = build_link('admin_teacher', rel='self')
        links += build_link('admin_teacher', rel='http://relations.highschool.com/teacherlist')
        links += build_link('admin_teacher', rel='http://relations.highschool.com/createteacher')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # get list of teachers from db
        teachers = session.query(Teacher).all()

        # check query result
        if not teachers:
            return build_response(error='No teachers found.', links=links), 404

        # build response
        t_list = []
        for t in teachers:
            t_list.append({'id': t.id, 'name': t.name, 'lastname': t.lastname})
        res = {'teachers': t_list}

        # more hypermedia
        for i in range(min(10, len(teachers))):
            links += build_link('admin_teacher_with_id', teacher_id=teachers[i].id,
                                rel='http://relations.highschool.com/teacher')

        return build_response(res, links=links)


@app.route('/admin/teacher/<int:teacher_id>/')
@auth_check
def admin_teacher_with_id(teacher_id):
    '''Info and index for this teacher'''

    # hypermedia
    links = build_link('admin_teacher_with_id', teacher_id=teacher_id, rel='self')
    links += build_link('admin_teacher', rel='http://relations.highschool.com/teacherlist')
    links += build_link('admin_teacher', rel='http://relations.highschool.com/createteacher')
    links += build_link('admin', rel='http://relations.highschool.com/index')

    # query info
    t = session.query(Teacher).get(teacher_id)

    # check query result
    if not t:
        return build_response(error='Teacher not found.', links=links), 404

    # build response
    t_obj = {'id': t.id, 'name': t.name, 'lastname': t.lastname}
    res = {'teacher': t_obj}

    # more hypermedia
    links += build_link('notification_teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/notificationlist')
    links += build_link('notification_teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/createnotification')

    build_response(res, links=links)


@app.route('/admin/parent/', methods=['GET', 'POST'])
@auth_check
def admin_parent():
    if request.method == 'POST':
        '''Create new parent account'''

        # hypermedia
        links = build_link('admin_parent', rel='self')
        links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
        links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        # check json content
        if 'name' not in data or 'lastname' not in data or 'username' not in data or 'password' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400

        existing = session.query(Account).filter_by(username=data['username'])
        if existing:
            return build_response(error='The username is already in use.', links=links), 400

        # create new object
        name = data['name']
        lastname = data['lastname']
        new_parent = Parent(name=name, lastname=lastname)

        # insert new parent in db
        session.add(new_parent)
        session.commit()

        # create new account object
        username = data['username']
        password = data['password']
        salt = os.urandom(16)
        hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        saved_password = salt.hex() + ':' + hash.hex()
        account = Account(username=username, password=saved_password, type='parent', parent_id=new_parent.id)

        # return parent, account objects
        p_obj = {'id': new_parent.id, 'name': name, 'lastname': lastname}
        a_obj = {'username': username, 'role': 'parent', 'parent_id': new_parent.id}
        res = {'parent': p_obj, 'account': a_obj}

        # more hypermedia
        links += build_link('admin_parent_with_id', parent_id=new_id, rel='http://relations.highschool.com/parent')

        return build_response(res, links=links), 201

    else:
        '''Show list of parents'''

        # get list of parents from db
        parents = session.query(Parent).all()

        # check query result
        if not parents:
            links = build_link('admin_parent', rel='self')
            links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
            links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
            links += build_link('admin', rel='http://relations.highschool.com/index')
            return build_response(error='No parents found.', links=links), 404

        # build response
        p_list = []
        for p in parents:
            p_list.append({'id': p.id, 'name': p.name, 'lastname': p.lastname})
        res = {'parents': p_list}

        # hypermedia
        links = build_link('admin_parent', rel='self')
        links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
        links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        for i in range(min(10, len(parents))):
            links += build_link('admin_parent_with_id', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/parent')

        return build_response(res, links=links)


@app.route('/admin/parent/<int:parent_id>/')
@auth_check
def admin_parent_with_id(parent_id):
    '''Info and index for this parent'''

    # query info
    t = session.query(Parent).get(parent_id)

    # check query result
    if not t:
        links = build_link('admin_parent_with_id', parent_id=parent_id, rel='self')
        links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
        links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        return build_response(error='Teacher not found.', links=links)

    # build response
    t_obj = {'id': t.id, 'name': t.name, 'lastname': t.lastname}
    res = {'teacher': t_obj}

    # hypermedia
    links = build_link('admin_parent_with_id', parent_id=parent_id, rel='self')
    links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
    links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
    links += build_link('admin', rel='http://relations.highschool.com/index')
    links += build_link('notification_parent_with_id', parent_id=parent_id,
                        rel='http://relations.highschool.com/notificationlist')
    links += build_link('notification_parent_with_id', parent_id=parent_id,
                        rel='http://relations.highschool.com/createnotification')
    links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
    links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/createpayment')

    build_response(res, links=links)


@app.route('/admin/class/')
@auth_check
def classes():
    '''Show list of classes'''

    # query classes
    classes = session.query(Class).all()

    # check query result
    if not classes:
        links = build_link('classes', rel='self')
        links += build_link('classes', rel='http://relations.highschool.com/classlist')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        return build_response(error='No classes found.', links=links), 404

    # response
    c_list = []
    for c in classes:
        c_list.append({'id': c.id, 'room': c.room, 'name': c.name})
    res = {'classes': c_list}

    # hypermedia
    links = build_link('classes', rel='self')
    links += build_link('classes', rel='http://relations.highschool.com/classlist')
    links += build_link('admin', rel='http://relations.highschool.com/index')
    for i in range(min(10, len(classes))):
        links += build_link('class_with_id', class_id=classes[i].id,
                            rel='http://relations.highschool.com/class')

    return build_response(res, links=links)


@app.route('/admin/class/<int:class_id>/')
@auth_check
def class_with_id(class_id):
    '''Show class info'''

    # query
    c = session.query(Class).get(class_id)

    # check query result
    if not c:
        links += build_link('classes', rel='http://relations.highschool.com/classlist')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        return build_response(error='Class not found.', links=links), 404

    # response
    c_obj = {'id': c.id, 'room': c.room, 'name': c.name}
    res = {'class': c_obj}

    # hypermedia
    links = build_link('class_with_id', class_id=class_id, rel='self')
    links += build_link('class_with_id', class_id=class_id, rel='http://relations.highschool.com/class')
    links += build_link('classes', rel='http://relations.highschool.com/classlist')
    links += build_link('admin', rel='http://relations.highschool.com/index')
    links += build_link('payment_class', class_id=class_id, rel='http://relations.highschool.com/paymentlist')
    links += build_link('payment_class', class_id=class_id, rel='http://relations.highschool.com/createpayment')
    links += build_link('notification_class', class_id=class_id, rel='http://relations.highschool.com/notificationlist')
    links += build_link('notification_class', class_id=class_id,
                        rel='http://relations.highschool.com/createnotification')
    links += build_link('class_student', class_id=class_id, rel='http://relations.highschool.com/studentlist')

    return build_response(res, links=links)


@app.route('/admin/class/<int:class_id>/student/')
@auth_check
def class_student(class_id):
    '''Show list of students in the class'''

    # check input
    c = session.query(Class).get(class_id)
    if not c:
        links = build_link('classes', rel='http://relations.highschool.com/classlist')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        return build_response(error='Class not found.', links=links), 404

    # query
    students = session.query(Student).filter_by(class_id=class_id).all()

    # check query result
    if not students:
        links = build_link('classes', rel='http://relations.highschool.com/classlist')
        links += build_link('admin', rel='http://relations.highschool.com/index')
        return build_response(error='No students found.', links=links), 404

    # build object
    s_list = []
    for s in students:
        s_list.append(
            {'id': s.id, 'name': s.name, 'lastname': s.lastname, 'parent_id': s.parent_id, 'class_id': s.class_id})
    res = {'students': s_list}

    # hypermedia
    links = build_link('classes', rel='http://relations.highschool.com/classlist')
    links += build_link('admin', rel='http://relations.highschool.com/index')
    links += build_link('class_student', class_id=class_id, rel='self')
    links += build_link('class_student', class_id=class_id, rel='http://relations.highschool.com/studentlist')
    for i in range(min(10, len(students))):
        links += build_link('student_with_id', student_id=students[i].id, rel='http://relations.highschool.com/student')

    return build_response(res, links=links)


@app.route('/admin/student/', methods=['GET', 'POST'])
@auth_check
def student():
    if request.method == 'POST':
        '''Create new student'''

        # hypermedia
        links = build_link('student', rel='self')
        links += build_link('student', rel='http://relations.highschool.com/studentlist')
        links += build_link('student', rel='http://relations.highschool.com/createstudent')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check json content
        if 'name' not in data or 'lastname' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        if 'parent_id' in data:
            parent_id = data['parent_id']
            p = session.query(Parent).get(parent_id)
            if not p:
                return build_response(error='Parent not found.', links=links), 400
        else:
            parent_id = None

        if 'class_id' in data:
            class_id = data['class_id']
            c = session.query(Class).get(class_id)
            if not c:
                return build_response(error='Class not found.', links=links), 400
        else:
            class_id = None

        # create new student
        name = data['name']
        lastname = data['lastname']
        new_student = Student(name=name, lastname=lastname, parent_id=parent_id, class_id=class_id)

        # insert new student in db
        session.add(new_student)
        session.commit()

        # return new object
        new_id = new_student.id
        s_obj = {'id': new_id, 'name': name, 'lastname': lastname, 'parent_id': parent_id, 'class_id': class_id}
        res = {'student': s_obj}

        # more hypermedia
        links += build_link('student_with_id', student_id=new_id, rel='http://relations.highschool.com/student')

        return build_response(res, links=links), 201

    else:
        '''Show list of students'''

        # hypermedia
        links = build_link('student', rel='self')
        links += build_link('student', rel='http://relations.highschool.com/studentlist')
        links += build_link('student', rel='http://relations.highschool.com/createstudent')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # query
        students = session.query(Student).all()

        # check query results
        if not students:
            return build_response(error='No students found.', links=links), 404

        # build object
        s_list = []
        for s in students:
            s_list.append(
                {'id': s.id, 'name': s.name, 'lastname': s.lastname, 'parent_id': s.parent_id, 'class_id': s.class_id})
        res = {'students': s_list}

        # more hypermedia
        for i in range(min(10, len(students))):
            links += build_link('student_with_id', student_id=students[i].id,
                                rel='http://relations.highschool.com/student')

        return build_response(res, links=links)


@app.route('/admin/student/<int:student_id>/', methods=['GET', 'PUT'])
@auth_check
def student_with_id(student_id):
    if request.method == 'PUT':
        '''Modify student (e.g. add parent, enroll in class)'''

        # hypermedia
        links = build_link('student_with_id', student_id=student_id, rel='self')
        links += build_link('student_with_id', student_id=student_id, rel='http://relations.highschool.com/student')
        links += build_link('student_with_id', student_id=student_id,
                            rel='http://relations.highschool.com/updatestudent')
        links += build_link('student', rel='http://relations.highschool.com/studentlist')
        links += build_link('student', rel='http://relations.highschool.com/createstudent')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        st = session.query(Student).get(student_id)
        if not st:
            return build_response(error='Student not found.', links=links), 404

        if 'name' not in data and 'lastname' not in data and 'parent_id' not in data and 'class_id' not in data:
            return build_response(error='No parameters valid for update were provided.', links=links), 400

        if 'parent_id' in data:
            parent_id = data['parent_id']
            if parent_id:
                p = session.query(Parent).get(parent_id)
                if not p:
                    return build_response(error='Parent not found.', links=links), 400

        if 'class_id' in data:
            class_id = data['class_id']
            if class_id:
                c = session.query(Class).get(class_id)
                if not c:
                    return build_response(error='Class not found.', links=links), 400

        # update database
        if 'parent_id' in data:
            st.parent_id = data['parent_id']

        if 'class_id' in data:
            st.class_id = data['class_id']

        if 'name' in data:
            st.name = data['name']

        if 'lastname' in data:
            st.lastname = data['lastname']

        # build response object
        s_obj = {'id': st.id, 'name': st.name, 'lastname': st.lastname, 'parent_id': st.parent_id,
                 'class_id': st.class_id}
        res = {'student': s_obj}

        # more hypermedia (parent, class)
        if st.parent_id:
            links += build_link('admin_parent_with_id', parent_id=st.parent_id,
                                rel='http://relations.highschool.com/parent')
        if st.class_id:
            links += build_link('class_with_id', class_id=st.class_id, rel='http://relations.highschool.com/class')

        return build_response(res, links=links)


    else:
        '''Show student info'''

        # hypermedia
        links = build_link('student_with_id', student_id=student_id, rel='self')
        links += build_link('student_with_id', student_id=student_id, rel='http://relations.highschool.com/student')
        links += build_link('student_with_id', student_id=student_id,
                            rel='http://relations.highschool.com/updatestudent')
        links += build_link('student', rel='http://relations.highschool.com/studentlist')
        links += build_link('student', rel='http://relations.highschool.com/createstudent')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # query
        st = session.query(Student).get(student_id)
        if not st:
            return build_response(error='Student not found.', links=links), 404

        # build response object
        s_obj = {'id': st.id, 'name': st.name, 'lastname': st.lastname, 'parent_id': st.parent_id,
                 'class_id': st.class_id}
        res = {'student': s_obj}

        # more hypermedia (parent, class)
        if st.parent_id:
            links += build_link('admin_parent_with_id', parent_id=st.parent_id,
                                rel='http://relations.highschool.com/parent')
        if st.class_id:
            links += build_link('class_with_id', class_id=st.class_id, rel='http://relations.highschool.com/class')

        return build_response(res, links=links)


@app.route('/admin/payment/', methods=['GET', 'POST'])
@auth_check
def payment():
    if request.method == 'POST':
        '''Create new payment for every parent'''

        # hypermedia
        links = build_link('payment', rel='self')
        links += build_link('payment', rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment', rel='http://relations.highschool.com/createpayment')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        if 'amount' not in data or 'date' not in data or 'reason' not in data:
            return build_response(error='The request must contain all the required parameters', links=links), 400

        # create new objects
        amount = data['amount']
        reason = data['reason']
        try:
            date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            return build_response(error='"date" must be a string following the format "yyyy-mm-dd hh:mm:ss"',
                                  links=links), 400

        parents = session.query(Parent).all()
        if not parents:
            return build_response(error='No parents found.', links=links), 404

        # create new objects
        new_payments = []
        for p in parents:
            new_paym = Payment(amount=amount, date=date, reason=reason, is_pending=True, parent_id=p.id)
            new_payments.append(new_paym)

        # insert new objects in database
        for p in new_payments:
            session.add(p)
        session.commit()

        # build response object
        p_obj = {'amount': amount, 'date': str(date), 'reason': reason, 'is_pending': True}
        res = {'payment': p_obj, 'number_created': len(new_payments)}

        # more hypermedia
        for i in range(min(5, len(parents))):
            links += build_link('payment_parent', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/createpayment')
            links += build_link('payment_parent', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/paymentlist')
        classes = session.query(Class).limit(5).all()
        for c in classes:
            links += build_link('payment_class', class_id=c.id, rel='http://relations.highschool.com/createpayment')
            links += build_link('payment_class', class_id=c.id, rel='http://relations.highschool.com/paymentlist')

        return build_response(res, links=links), 201

    else:
        '''List all payments'''

        # hypermedia
        links = build_link('payment', rel='self')
        links += build_link('payment', rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment', rel='http://relations.highschool.com/createpayment')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # query
        payments = session.query(Payment).all()

        # check query results
        if not payments:
            return build_response(error='No payments found.', links=links), 404

        # create response object
        p_list = []
        for p in payments:
            p_obj = {'id': p.id, 'amount': p.amount, 'date': str(p.date), 'reason': p.reason,
                     'is_pending': p.is_pending, 'parent_id': p.parent_id}
            p_list.append(p_obj)
        res = {'payments': p_list}

        # more hypermedia
        for i in range(min(5, len(payments))):
            links += build_link('admin_parent_with_id', parent_id=payments[i].parent_id,
                                rel='http://relations.highschool.com/parent')
        parents = session.query(Parents).limit(3).all()
        for p in parents:
            links += build_link('payment_parent', parent_id=p.id, rel='http://relations.highschool.com/createpayment')
            links += build_link('payment_parent', parent_id=p.id, rel='http://relations.highschool.com/paymentlist')
        classes = session.query(Class).limit(3).all()
        for c in classes:
            links += build_link('payment_class', class_id=c.id, rel='http://relations.highschool.com/createpayment')
            links += build_link('payment_class', class_id=c.id, rel='http://relations.highschool.com/paymentlist')

        return build_response(res, links=links)


@app.route('/admin/payment/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def payment_parent(parent_id):
    if request.method == 'POST':
        '''Create a new payment for a parent'''

        # hypermedia
        links = build_link('payment_parent', parent_id=parent_id, rel='self')
        links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/createpayment')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        parent = session.query(Parent).get(parent_id)
        if not parent:
            return build_response(error='Parent not found.', links=links), 404

        if 'amount' not in data or 'date' not in data or 'reason' not in data:
            return build_response(error='The request must contain all the required parameters', links=links), 400

        # create new objects
        amount = data['amount']
        reason = data['reason']
        try:
            date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            return build_response(error='"date" must be a string following the format "yyyy-mm-dd hh:mm:ss"',
                                  links=links), 400

        # create new object
        new_payment = Payment(amount=amount, date=date, reason=reason, is_pending=True, parent_id=parent_id)

        # insert new object in database
        session.add(new_payment)
        session.commit()

        # build response object
        p_obj = {'amount': amount, 'date': str(date), 'reason': reason, 'is_pending': True, 'parent_id': parent_id}
        res = {'payment': p_obj}

        # more hypermedia
        links += build_link('admin_parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/parent')

        return build_response(res, links=links), 201

    else:
        '''List payments for a parent'''

        # hypermedia
        links = build_link('payment_parent', parent_id=parent_id, rel='self')
        links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/createpayment')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check input
        parent = session.query(Parent).get(parent_id)
        if not parent:
            return build_response(error='Parent not found.', links=links), 404

        # query
        payments = session.query(Payment).filter_by(parent_id=parent_id)

        # check query result
        if not payments:
            return build_response(error='No payments found.', links=links), 404

        # create response object
        p_list = []
        for p in payments:
            p_obj = {'id': p.id, 'amount': p.amount, 'date': str(p.date), 'reason': p.reason,
                     'is_pending': p.is_pending, 'parent_id': p.parent_id}
            p_list.append(p_obj)
        res = {'payments': p_list}

        # more hypermedia
        links += build_link('admin_parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/parent')

        return build_response(res, links=links)


@app.route('/admin/payment/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def payment_class(class_id):
    if request.method == 'POST':
        '''Create a new payment for a class'''

        # hypermedia
        links = build_link('payment_class', class_id=class_id, rel='self')
        links += build_link('payment_class', class_id=class_id, rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment_class', class_id=class_id, rel='http://relations.highschool.com/createpayment')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        c = session.query(Class).get(class_id)
        if not c:
            return build_response(error='Class not found.', links=links), 404

        if 'amount' not in data or 'date' not in data or 'reason' not in data:
            return build_response(error='The request must contain all the required parameters', links=links), 400

        parents = session.query(Parent).join(Student.parent_id).filter(Student.class_id == class_id).all()
        if not parents:
            return build_response(error='No parents found.', links=links), 404

        # create new objects
        new_payments = []
        for p in parents:
            new_paym = Payment(amount=amount, date=date, reason=reason, is_pending=True, parent_id=p.id)
            new_payments.append(new_paym)

        # insert new objects in database
        for p in new_payments:
            session.add(p)
        session.commit()

        # build response object
        p_obj = {'amount': amount, 'date': str(date), 'reason': reason, 'is_pending': True}
        res = {'payment': p_obj, 'number_created': len(new_payments)}

        # more hypermedia
        links += build_link('class_with_id', class_id=class_id, rel='http://relations.highschool.com/class')

        return build_response(res, links=links), 201

    else:
        '''List payments for a class'''

        # hypermedia
        links = build_link('payment_class', class_id=class_id, rel='self')
        links += build_link('payment_class', class_id=class_id, rel='http://relations.highschool.com/paymentlist')
        links += build_link('payment_class', class_id=class_id, rel='http://relations.highschool.com/createpayment')
        links += build_link('admin', rel='http://relations.highschool.com/index')

        # check input
        c = session.query(Class).get(class_id)
        if not c:
            return build_response(error='Class not found.', links=links), 404

        # query
        payments = session.query(Payment).join(Parent).join(Student).filter(Student.class_id == class_id).all()

        # check query results
        if not payments:
            return build_response(error='No payments found.', links=links), 404

        # create response object
        p_list = []
        for p in payments:
            p_obj = {'id': p.id, 'amount': p.amount, 'date': str(p.date), 'reason': p.reason,
                     'is_pending': p.is_pending, 'parent_id': p.parent_id}
            p_list.append(p_obj)
        res = {'payments': p_list}

        # more hypermedia
        links += build_link('class_with_id', class_id=class_id, rel='http://relations.highschool.com/class')

        return build_response(res, links=links)


@app.route('/admin/notification/', methods=['GET', 'POST'])
@auth_check
def notification():
    if request.method == 'POST':
        '''Create a school-wide notification'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='all')

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'], 'scope': 'all'}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201

    else:
        '''List school-wide notifications'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='all').all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/parent/', methods=['GET', 'POST'])
def notification_parents():
    if request.method == 'POST':
        '''Create a notification for all parents'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='parents')

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'parents'}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201

    else:
        '''List notifications for all parents'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='parents').all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def notification_parent_with_id(parent_id):
    if request.method == 'POST':
        '''Create a notification for a single parent'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        parent = session.query(Parent).get(parent_id)
        if not parent:
            return build_response(error='Parent not found.', links=links), 404

        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='one_parent',
                                        parent_id=parent_id)

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'one_parent', 'parent_id': parent_id}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201
        
    else:
        '''List notifications for this parent'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='one_parent').filter_by(parent_id=parent_id).all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope, 'parent_id': parent_id})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/teacher/', methods=['GET', 'POST'])
@auth_check
def notification_teachers():
    if request.method == 'POST':
        '''Create a notification for all teachers'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='teachers')

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'teachers'}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201
        
    else:
        '''List notifications for all teachers'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='teachers').all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/teacher/<int:teacher_id>/', methods=['GET', 'POST'])
@auth_check
def notification_teacher_with_id(teacher_id):
    if request.method == 'POST':
        '''Create a notification for a single teacher'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='one_teacher',
                                        teacher_id=teacher_id)

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'one_teacher', 'teacher_id': teacher_id}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201
        
    else:
        '''List notifications for a single teacher'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='one_teacher').filter_by(teacher_id=teacher_id).all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope, 'teacher_id': teacher_id})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def notification_class(class_id):
    if request.method == 'POST':
        '''Create a class-wide notification'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        c = session.query(Class).get(class_id)
        if not c:
            return build_response(error='Class not found.', links=links), 404

        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='class',
                                        class_id=class_id)

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'class', 'class_id': class_id}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201
        
    else:
        '''List class-wide notifications'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='class').filter_by(class_id=class_id).all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope, 'class_id': class_id})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/class/<int:class_id>/parents/', methods=['GET', 'POST'])
@auth_check
def notification_class_parents(class_id):
    if request.method == 'POST':
        '''Create a notification for the parents in a class'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        c = session.query(Class).get(class_id)
        if not c:
            return build_response(error='Class not found.', links=links), 404

        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='class_parents',
                                        class_id=class_id)

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'class_parents', 'class_id': class_id}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201
        
    else:
        '''List all notifications for the parents in a class'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='class_parents').filter_by(class_id=class_id).all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope, 'class_id': class_id})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)


@app.route('/admin/notification/class/<int:class_id>/teachers/', methods=['GET', 'POST'])
@auth_check
def notification_class_teachers(class_id):
    if request.method == 'POST':
        '''Create a notification for the teachers in a class'''

        # hypermedia
        # TODO
        links = []

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check input
        c = session.query(Class).get(class_id)
        if not c:
            return build_response(error='Class not found.', links=links), 404

        if 'text' not in data:
            return build_response(error='The request must contain all the required parameters.', links=links), 400

        # create new object
        new_notification = Notification(date=datetime.datetime.now(), text=data['text'], scope='class_teachers',
                                        class_id=class_id)

        # insert object in database
        session.add(new_notification)
        session.commit()

        # build response object
        n_obj = {'id': new_notification.id, 'date': str(new_notification.date), 'text': data['text'],
                 'scope': 'class_teachers', 'class_id': class_id}
        res = {'notification': n_obj}

        # more hypermedia

        return build_response(res, links=links), 201
        
    else:
        '''List all notifications for the teachers in a class'''

        # hypermedia
        # TODO
        links = []

        # query
        nots = session.query(Notification).filter_by(scope='class_teachers').filter_by(class_id=class_id).all()

        # check query results
        if not nots:
            return build_response(error='No notifications found for this scope.', links=links), 404

        # build response object
        n_list = []
        for n in nots:
            n_list.append({'id': n.id, 'date': str(n.date), 'text': n.text, 'scope': n.scope, 'class_id': class_id})
        res = {'notifications': n_list}

        # more hypermedia

        return build_response(res, links=links)

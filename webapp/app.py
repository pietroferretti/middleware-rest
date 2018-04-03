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
    resp.headers["Content-Type"] = 'application/vnd.stocazzo+json; schema="{}"'.format(request.url_root.rstrip('/') + url_for('schema', path=RESPONSE_SCHEMA))
    return resp

def build_link(endpoint, rel='http://relations.highschool.com/linkrelation', **kwargs):
    # TODO get schema for endpoint
    return [{'link': request.url_root.rstrip('/') + url_for(endpoint, **kwargs), 
            'rel': rel}]


# default error handlers
@app.errorhandler(400)
def bad_request(e):
    # hypermedia back to endpoint
    links = [{'link': request.url, 'rel': 'self'}]
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
    # hypermedia back to index
    links = build_link('login', rel='http://relations.highschool.com/login')
    if DEBUG:
        return build_response(error=str(e), links=links), 403
    else:
        return build_response(error='Forbidden', links=links), 403

@app.errorhandler(404)
def page_not_found(e):
    # hypermedia back to index
    links = build_link('login', rel='http://relations.highschool.com/login')
    if DEBUG:
        return build_response(error=str(e), links=links), 404
    else:
        return build_response(error='Page Not Found', links=links), 404

@app.errorhandler(405)
def method_not_allowed(e):
    # hypermedia back to endpoint
    links = [{'link': request.url, 'rel': 'self'}]
    if DEBUG:
        return build_response(error=str(e), links=links), 405
    else:
        return build_response(error='Method Not Allowed', links=links), 405


@app.errorhandler(500)
def server_error(e):
    # hypermedia back to index, endpoint
    links = [{'link': request.url, 'rel': 'self'}]
    links += build_link('login', rel='http://relations.highschool.com/login')
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
        if not clienttoken or not 'scopes' in clienttoken:
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
    return build_response(d)


@app.route('/schema/<path:path>')
def schema(path):
    '''Returns the schema with the given filename'''
    return send_from_directory('schemas', path, mimetype='application/json')


@app.route('/login/', methods=['POST'])
def login():
    # check content type
    try:
        data = request.get_json()
    except TypeError:
        links = build_link('login', rel='http://relations.highschool.com/login')
        links += build_link('login', rel='self')
        return build_response(None, error='The request was not valid JSON.', links=links), 400
    # check json content
    if 'username' not in data or 'password' not in data:
        links = build_link('login', rel='http://relations.highschool.com/login')
        links += build_link('login', rel='self')
        return build_response(None, error='The JSON structure must contain all the requested parameters.', links=links), 400
    # get username, password
    username = data['username']
    password = data['password']

    # check if username and password exist in the database
    # TODO

    # check if admin, teacher or parent
    # assign different scopes in each case
    role = 'teacher'
    # TODO get role from database
    if role == 'admin':
        scopes = ['/admin/', '/teacher/', '/parent/']
        #links = ['link': 'link': request.url_root.rstrip('/') + url_for('admin'),
        #         'rel': 'http://relations.highschool.com/index']
        links = build_link('admin', rel='http://relations.highschool.com/index')
        links += build_link('login', rel='self')
    elif role == 'teacher':
        # TODO select id from database
        teacher_id = 1234
        scopes = ['/teacher/{}/'.format(teacher_id)]
        #links = [{'link': request.url_root.rstrip('/') + url_for('teacher_with_id', teacher_id=teacher_id),
        #          'rel': 'http://relations.highschool.com/index'}]
        links = build_link('teacher_with_id', teacher_id=teacher_id,
                           rel='http://relations.highschool.com/index')
        links += build_link('login', rel='self')
    elif role == 'parent':
        # TODO select id from database
        parent_id = 5687
        scopes = ['/parent/{}/'.format(parent_id)]
        #links = [{'link': request.url_root.rstrip('/') + url_for('parent_with_id', parent_id=parent_id),
        #          'rel': 'http://relations.highschool.com/index'}]
        links = build_link('parent_with_id', parent_id=parent_id,
                           rel='http://relations.highschool.com/index')
        links += build_link('login', rel='self')
    else:
        raise ValueError('Role "{}" not recognized!'.format(role))

    # save authorized endpoints in a cryptografically secure client side cookie
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
    teacher = session.query(Teacher).filter_by(id=teacher_id).first()
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
        teacher = session.query(Teacher).filter_by(id=teacher_id).first()
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
        teacher = session.query(Teacher).filter_by(id=teacher_id).first()
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
    teacher = session.query(Teacher).filter_by(id=teacher_id).first()
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
        links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=cl[i]['c_id'],
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

    c = session.query(Class).filter_by(id=class_id).first()
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

    c = session.query(Class).filter_by(id=class_id).first()
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

        date = datetime.strptime(data['date'], '%d %m %Y')
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
            grade.date = datetime.strptime(data['date'], '%d %m %Y')

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
            date = datetime.strptime(grade['date'], '%d %m %Y')
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

@app.route('/teacher/<int:teacher_id>/appointment/')
@auth_check
def teacher_appointment(teacher_id):
    '''show list of appointments for a teacher'''
    appointments_list = session.query(Appointment).filter_by(teacher_id=teacher_id).all()

    if not appointments_list:
        return build_response(None, error='Appointments not found.'), 404

    appointments = []
    for a in appointments_list:
        parent = session.query(Parent).filter_by(id=a.parent_id).one()
        appointments.append({'appointment': {'id': a.id, 'date': a.date, 'room': a.room,
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
            appointment.date = datetime.strptime(data['date'], '%d %m %Y')

        if 'room' in data:
            appointment.room = data['room']

        if 'parent_id' in data:
            appointment.parent_id = int(data['parent_id'])

        session.commit()
        return build_response({'message': 'Update successful.'})
        
    else:
        '''show appointment info'''
        parent = session.query(Parent).filter_by(id=appointment.parent_id).one()

        return build_response({'appointment': {'id': appointment.id, 'date': appointment.date, 'room': appointment.room,
                                               'parent': {'name': parent.name,
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

    if not parent:
        return build_response(None, 'Parent not found.')

    student = session.query(Student).filter_by(parent_id=parent_id).filter_by(id=student_id).one()

    if not student:
        return build_response(None, 'Student not found.')

    c = session.query(Class).filter_by(id=student.class_id).first()

    if not c:
        res = 'Not enrolled.'
    


@app.route('/parent/<int:parent_id>/appointment/', methods=['GET', 'POST'])
@auth_check
def parent_appointment(parent_id):
    if request.method == 'POST':
        '''create new appointment'''
        pass
    else:
        '''show all appointments'''
        pass
# TODO calendar-like support

@app.route('/parent/<int:parent_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
@auth_check
def parent_appointment_with_id(parent_id, appointment_id):
    if request.method == 'PUT':
        '''edit appointment'''
        pass
    else:
        '''show appointment info'''
        pass

@app.route('/parent/<int:parent_id>/payment/')
@auth_check
def parent_payment(parent_id):
    '''list all payments, paid or pending'''
    pass

@app.route('/parent/<int:parent_id>/payment/paid/')
@auth_check
def parent_payment_paid(parent_id):
    '''list old paid payments'''
    pass

@app.route('/parent/<int:parent_id>/payment/pending/')
@auth_check
def parent_payment_pending(parent_id):
    '''list pending payments'''
    pass

@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/')
@auth_check
def parent_payment_with_id(parent_id, payment_id):
    '''show payment info'''
    pass

@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/pay/', methods=['POST'])
@auth_check
def parent_pay(parent_id, payment_id):
    '''magic payment endpoint'''
    pass

@app.route('/parent/<int:parent_id>/notifications/')
@auth_check
def parent_notifications(parent_id):
    '''show notifications for this parent'''
    pass


'''ADMIN STUFF'''

@app.route('/admin/', methods=['GET', 'POST'])
@auth_check
def admin():
    if request.method == 'POST':
        '''create new admin account'''
        pass
    else:
        '''list admin accounts?'''
        pass


@app.route('/admin/teacher/', methods=['GET', 'POST'])
@auth_check
def teacher():
    '''admin endpoint'''
    if request.method == 'POST':
        '''create a new teacher'''
        # validate json TODO

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400
        # check json content
        if 'name' not in data or 'lastname' not in data or 'pwd' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400

        # create new teacher object
        name = data['name']
        lastname = data['lastname']
        pwd = data['pwd']
        new_teacher = Teacher(name=name, lastname=lastname, pwd=pwd)
        # insert new teacher in db
        session.add(new_teacher)
        session.commit()
        # return confirmation, new id
        new_id = new_teacher.id

        links = []
        link = {'link': 'http://asdfasdfdasf.com/teacher/id/data', 'rel': 'http://relations.highschool.com/data'}
        links.append(link)

        return build_response({'id': new_id}, links=links), 201

    else:
        '''list of teachers'''
        # get list of teachers from db
        teachers = session.query(Teacher).all()
        res = []
        for t in teachers:
            res.append({'id': t.id, 'name': t.name, 'lastname': t.lastname})
        # return structured list
        return build_response(res)

@app.route('/admin/parent/', methods=['GET', 'POST'])
@auth_check
def parent():
    '''admin endpoint'''
    if request.method == 'POST':
        '''create new parent account'''
        # validate json TODO

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400
        # check json content
        if 'name' not in data or 'lastname' not in data or 'pwd' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400

        # create new object
        name = data['name']
        lastname = data['lastname']
        pwd = data['pwd']
        new_parent = Parent(name=name, lastname=lastname, pwd=pwd)
        # insert new teacher in db
        session.add(new_parent)
        session.commit()
        # return confirmation, new id
        new_id = new_parent.id
        return build_response({'id': new_id}), 201

    else:
        '''show list of parents'''
        parents = session.query(Parent).all()
        res = []
        for p in parents:
            res.append({'id': p.id, 'name': p.name, 'lastname': p.lastname})
        # return structured list
        return build_response(res)

@app.route('/admin/class/')
@auth_check
def classes():
    '''show list of classes'''
    '''POST create new classes non c'e' nelle specifiche'''
    pass

@app.route('/admin/class/<int:class_id>/')
@auth_check
def class_with_id(class_id):
    '''show class info? non nelle specifiche'''
    pass

@app.route('/admin/class/<int:class_id>/student/', methods=['GET', 'POST'])
@auth_check
def class_student(class_id):
    if request.method == 'POST':
        '''create new student'''
        pass
    else:
        '''show list of students in the class'''

@app.route('/admin/student/')
@auth_check
def student():
    '''show list of students (non nelle specifiche)'''
    pass

@app.route('/admin/student/<int:student_id>/')
@auth_check
def student_with_id(student_id):
    '''show student info (spostare in /class/student/?'''
    pass

@app.route('/admin/payment/', methods=['GET', 'POST'])
@auth_check
def payment():
    if request.method == 'POST':
        '''create new payment for the whole school'''
        pass
    else:
        '''list school-wide payments'''
        pass

@app.route('/admin/payment/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def payment_parent(parent_id):
    if request.method == 'POST':
        '''create new payment for a parent'''
        pass
    else:
        '''list payments for a parent'''
        pass

@app.route('/admin/payment/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def payment_class(class_id):
    if request.method == 'POST':
        '''create new payment for a class'''
        pass
    else:
        '''list payments for a class'''
        pass

@app.route('/admin/notification/', methods=['GET', 'POST'])
@auth_check
def notification():
    #FIXME DELETE?
    if request.method == 'POST':
        '''create school-wide notification'''
        pass
    else:
        '''list school-wide notifications'''
        pass

@app.route('/admin/notification/parent/', methods=['GET', 'POST'])
def notification_parents():
    if request.method == 'POST':
        '''create notification to all parents'''
        pass
    else:
        '''list notifications to all parents'''
        pass

@app.route('/admin/notification/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def notification_parent_with_id(parent_id):
    if request.method == 'POST':
        '''create parent notification'''
        pass
    else:
        '''list parent notifications'''
        pass

@app.route('/admin/notification/teacher/', methods=['GET', 'POST'])
@auth_check
def notification_teachers():
    if request.method == 'POST':
        '''create notification to all teachers'''
        pass
    else:
        '''list notifications to all teachers'''
        pass

@app.route('/admin/notification/teacher/<int:teacher_id>/', methods=['GET', 'POST'])
@auth_check
def notification_teacher_with_id(teacher_id):
    if request.method == 'POST':
        '''create notification for a teacher'''
        pass
    else:
        '''list a teacher's notifications'''
        pass

@app.route('/admin/notification/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def notification_class(class_id):
    if request.method == 'POST':
        '''create class-wide notification'''
        pass
    else:
        '''list class-wide notifications'''
        pass

@app.route('/admin/notification/class/<int:class_id>/parents/', methods=['GET', 'POST'])
@auth_check
def notification_class_parents(class_id):
    if request.method == 'POST':
        '''create a notification for the parents in a class'''
        pass
    else:
        '''list all notifications for the parents in a class'''
        pass

@app.route('/admin/notification/class/<int:class_id>/teachers/', methods=['GET', 'POST'])
@auth_check
def notification_class_teachers(class_id):
    if request.method == 'POST':
        '''create a notification for the teachers in a class'''
        pass
    else:
        '''list all notifications for the teachers in a class'''
        pass

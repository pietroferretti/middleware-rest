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

from flask import Flask, request, jsonify, abort
from flask import session as clienttoken
from functools import wraps
from db.db_declarative import *

import IPython

DEBUG = False

app = Flask(__name__)
app.secret_key = '\x8d)2m_\xa4\x8e\xe1\xaa\x8ca\xbd\xc6\xed@\xcbxw~\xe8x\xa2\xa2^'

def build_response(content, restype='json', error=None):
    '''Builds a HTTP response with the specified content in a JSON (TODO or xml) envelope'''
    # TODO add hypermedia as parameter
    if restype == 'json':
        resp_dict = {'content': content, 'error': error}
        return jsonify(resp_dict)
    else:
        raise ValueError('Response type {} not recognized'.format(restype))


# default error handlers
# TODO add hypermedia to error handlers
@app.errorhandler(400)
def bad_request(e):
    # hypermedia back to endpoint
    return build_response(None, error='Bad Request'), 400

@app.errorhandler(401)
def authorization_required(e):
    # TODO add hypermedia redirecting to /login
    return build_response(None, error='Authorization Required'), 401

@app.errorhandler(403)
def forbidden(e):
    # hypermedia back to index
    return build_response(None, error='Forbidden'), 403

@app.errorhandler(404)
def page_not_found(e):
    # hypermedia back to index
    return build_response(None, error='Page Not Found'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    # hypermedia back to endpoint
    return build_response(None, error='Method Not Allowed'), 405

@app.errorhandler(500)
def server_error(e):
    # hypermedia back to index, endpoint
    return build_response(None, error='Internal Server Error'), 500

# define authorization check decorator
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


# define login endpoint
@app.route('/login', methods=['POST'])
def login():
    # check content type
    try:
        data = request.get_json()
    except TypeError:
        return build_response(None, error='The request was not valid JSON.'), 400
    # check json content
    if 'username' not in data or 'password' not in data:
        return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400
    # get username, password
    username = data['username']
    password = data['password']

    # check if username and password exist in the database
    # TODO

    # check if admin, teacher or parent
    # assign different scopes in each case
    role = ''
    if role == 'admin':
        scopes = ['/admin', '/teacher/', '/parent/', '/student/', '/class/', '/notification/', '/payment/']
    elif role == 'teacher':
        # TODO select id from database
        teacher_id = 1234
        scopes = ['/teacher/{}/'.format(teacher_id)]
    elif role == 'parent':
        # TODO select id from database
        parent_id = 5687
        scopes = ['/parent/{}/'.format(parent_id)]

    # save authorized endpoints in a cryptografically secure client side cookie
    clienttoken['scopes'] = scopes

    return build_response({'result': 'Login successful.', 'username': data['username']})

# TODO add auth check to all endpoints (except /, /login)
# copia e incolla


@app.route('/')
def index():
    '''Root endpoint'''
    # hypermedia qui?
    d = {'data':2, 'error':None}
    return jsonify(d)
    #return 'Hello, World!'


'''TEACHER'''

@app.route('/teacher/', methods=['GET', 'POST'])
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
        # open db session
        session = create_session()
        # insert new teacher in db
        session.add(new_teacher)
        session.commit()
        # return confirmation, new id
        new_id = new_teacher.id
        return build_response({'id': new_id}), 201

    else:
        '''list of teachers'''
        # open db session
        session = create_session()
        # get list of teachers from db
        teachers = session.query(Teacher).all()
        res = []
        for t in teachers:
            res.append({'id': t.id, 'name': t.name, 'lastname': t.lastname})
        # return structured list
        return build_response(res)


@app.route('/teacher/<int:teacher_id>/')
@auth_check
def teacher_with_id(teacher_id):
    '''teacher main index: show teacher info, hypermedia'''
    # create db session
    session = create_session()
    # get teacher with id
    teacher = session.query(Teacher).filter_by(id=teacher_id).first()
    # check if the teacher was found
    if not teacher:
        # OAuth should avoid this
        return build_response(None, error='Teacher id not found.'), 404
    # return response
    res = {'name': teacher.name, 
           'lastname': teacher.lastname}
    # TODO ritorna tutto cio' che puo' servire a un teacher?
    # numero di classi, subject, appointments?
    # e' ridondante con /data/, /class/, ecc.
    # possiamo usarlo magari solo per l'hypermedia

    return build_response(res)


@app.route('/teacher/<int:teacher_id>/data/', methods=['GET', 'PUT'])
@auth_check
def teacher_data(teacher_id):
    if request.method == 'PUT':
        '''modify personal data'''
        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        # check json content
        if 'name' not in data and 'lastname' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400
        # TODO check if type is str (sempre in validazione json?)
        session 
        if 'name' in data:
            newname = data['name']

        newname = data['name']
        newlastname = data['lastname']
        session = create_session()
        teacher = session.query(Teacher).filter_by(id=teacher_id).first()
        if 'name' in data:
            teacher.name = data['name']
        if 'lastname' in data:
            teacher.lastname = data['lastname']
        session.commit()
        return build_response({'message':'Update successful.'})
        # TODO ha senso 'message'?
    else:
        '''show personal data'''
        # create session
        session = create_session()
        # get data from teachers with id
        teacher = session.query(Teacher).filter_by(id=teacher_id).first()
        # check if the teacher was found
        if not teacher:
            # OAuth should avoid this
            return build_response(None, error='Teacher id not found.'), 404
        res = {'name': teacher.name, 
               'lastname': teacher.lastname}
        return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/')
@auth_check
def teacher_class(teacher_id):
    '''show list of classes for the specific teacher'''
    pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/')
@auth_check
def teacher_class_with_id(teacher_id, class_id):
    '''show class info for that teacher (students, subjects, timetable)'''
    pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/')
@auth_check
def teacher_subject(teacher_id, class_id):
    '''show list of subject taught by a teacher in a class'''
    pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/')
@auth_check
def teacher_subject_with_id(teacher_id, class_id, subject_id):
    '''show subject info taught by a teacher'''
    pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/')
@auth_check
def teacher_student(teacher_id, class_id, subject_id):
    '''show list of students for a subject taught by a teacher'''
    pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/<int:student_id>/grade/', methods=['GET', 'POST', 'PUT'])
@auth_check
def teacher_student_grades(teacher_id, class_id, subject_id, student_id):
    if request.method == 'POST':
        '''add new grade'''
        pass
    elif request.method == 'PUT':
        '''edit old grade'''
        # FIXME aggiungere un /grade/<grade_id> ?
        pass
    else:
        '''show grades list'''

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/grade/', methods=['GET', 'POST'])
@auth_check
def teacher_class_grades(teacher_id, class_id, subject_id):
    if request.method == 'POST':
        '''add new list of grades for the whole class'''
        pass
    else:
        '''show grades for the whole class for that subject'''
        pass

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
    pass

@app.route('/teacher/<int:teacher_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
@auth_check
def teacher_appointment_with_id(teacher_id, appointment_id):
    if request.method == 'PUT':
        '''edit appointment'''
        pass
    else:
        '''show appointment info'''
        pass

@app.route('/teacher/<int:teacher_id>/notifications/')
@auth_check
def teacher_notifications(teacher_id):
    '''show notifications for this teacher'''
    pass


'''PARENT'''

@app.route('/parent/', methods=['GET', 'POST'])
@auth_check
def parent():
    '''admin endpoint'''
    if request.method == 'POST':
        '''create new parent account'''
        pass
    else:
        '''show list of parents'''

@app.route('/parent/<int:parent_id>/')
@auth_check
def parent_with_id(parent_id):
    '''parent main index: parent info, hypermedia'''
    pass

@app.route('/parent/<int:parent_id>/data/', methods=['GET', 'PUT'])
@auth_check
def parent_data(parent_id):
    if request.method == 'PUT':
        '''edit parent personal data'''
        # check content type
        # if == json
        # parse json
        data = request.get_json()
        newname = data['name']
        newlastname = data['lastname']
        session = create_session()
        parent = session.query(Parent).filter(Parent.id == int(parent_id)).first()
        parent.name = newname
        parent.lastname = newlastname
        session.commit()
        return jsonify('ok')
    else:
        '''show parent personal data'''
        # create session
        session = create_session()
        # get data from teachers with id
        parent = session.query(Parent).filter(Parent.id == int(parent_id)).first()
        resp = {}
        resp['name'] = parent.name
        resp['lastname'] = parent.lastname
        return jsonify(resp)

@app.route('/parent/<int:parent_id>/child/')
@auth_check
def parent_child(parent_id):
    '''list children of parent'''
    pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/')
@auth_check
def parent_child_with_id(parent_id, student_id):
    '''show info of student?'''
    pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/data/', methods=['GET', 'PUT'])
@auth_check
def parent_child_data(parent_id, student_id):
    if request.method == 'PUT':
        '''edit child personal data'''
        pass
    else:
        '''show child personal data'''
        pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/grades/')
@auth_check
def parent_child_grades(parent_id, student_id):
    '''show all grades of the student'''
    pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/teachers/')
@auth_check
def parent_child_teacher(parent_id, student_id):
    '''list all child's teachers'''
    pass

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
        '''list admin accounts'''
        pass

@app.route('/class/')
@auth_check
def classes():
    '''show list of classes'''
    '''POST create new classes non c'e' nelle specifiche'''
    pass

@app.route('/class/<int:class_id>/')
@auth_check
def class_with_id(class_id):
    '''show class info? non nelle specifiche'''
    pass

@app.route('/class/<int:class_id>/student/', methods=['GET', 'POST'])
@auth_check
def class_student(class_id):
    if request.method == 'POST':
        '''create new student'''
        pass
    else:
        '''show list of students in the class'''

@app.route('/student/')
@auth_check
def student():
    '''show list of students (non nelle specifiche)'''
    pass

@app.route('/student/<int:student_id>/')
@auth_check
def student_with_id(student_id):
    '''show student info (spostare in /class/student/?'''
    pass

@app.route('/payment/', methods=['GET', 'POST'])
@auth_check
def payment():
    if request.method == 'POST':
        '''create new payment for the whole school'''
        pass
    else:
        '''list school-wide payments'''
        pass

@app.route('/payment/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def payment_parent(parent_id):
    if request.method == 'POST':
        '''create new payment for a parent'''
        pass
    else:
        '''list payments for a parent'''
        pass

@app.route('/payment/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def payment_class(class_id):
    if request.method == 'POST':
        '''create new payment for a class'''
        pass
    else:
        '''list payments for a class'''
        pass

@app.route('/notification/', methods=['GET', 'POST'])
@auth_check
def notification():
    #FIXME DELETE?
    if request.method == 'POST':
        '''create school-wide notification'''
        pass
    else:
        '''list school-wide notifications'''
        pass

@app.route('/notification/parent/', methods=['GET', 'POST'])
def notification_parents():
    if request.method == 'POST':
        '''create notification to all parents'''
        pass
    else:
        '''list notifications to all parents'''
        pass

@app.route('/notification/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def notification_parent_with_id(parent_id):
    if request.method == 'POST':
        '''create parent notification'''
        pass
    else:
        '''list parent notifications'''
        pass

@app.route('/notification/teacher/', methods=['GET', 'POST'])
@auth_check
def notification_teachers():
    if request.method == 'POST':
        '''create notification to all teachers'''
        pass
    else:
        '''list notifications to all teachers'''
        pass

@app.route('/notification/teacher/<int:teacher_id>/', methods=['GET', 'POST'])
@auth_check
def notification_teacher_with_id(teacher_id):
    if request.method == 'POST':
        '''create notification for a teacher'''
        pass
    else:
        '''list a teacher's notifications'''
        pass

@app.route('/notification/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def notification_class(class_id):
    if request.method == 'POST':
        '''create class-wide notification'''
        pass
    else:
        '''list class-wide notifications'''
        pass

@app.route('/notification/class/<int:class_id>/parents/', methods=['GET', 'POST'])
@auth_check
def notification_class_parents(class_id):
    if request.method == 'POST':
        '''create a notification for the parents in a class'''
        pass
    else:
        '''list all notifications for the parents in a class'''
        pass

@app.route('/notification/class/<int:class_id>/teachers/', methods=['GET', 'POST'])
@auth_check
def notification_class_teachers(class_id):
    if request.method == 'POST':
        '''create a notification for the teachers in a class'''
        pass
    else:
        '''list all notifications for the teachers in a class'''
        pass

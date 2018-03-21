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

from flask import Flask
from flask import request
from flask import jsonify
app = Flask(__name__)

from db.db_declarative import *

import IPython

def build_response(content, restype='json', error=None):
    '''Builds a HTTP response with the specified content in a JSON (TODO or xml) envelope'''
    # TODO add hypermedia as parameter
    if restype == 'json':
        resp_dict = {'content': content, 'error': error}
        return jsonify(resp_dict)
    else:
        raise ValueError('Response type {} not recognized'.format(restype))


@app.route('/')
def index():
    '''Root endpoint'''
    # hypermedia qui?
    d = {'data':2, 'error':None}
    return jsonify(d)
    #return 'Hello, World!'


'''TEACHER'''

@app.route('/teacher/', methods=['GET', 'POST'])
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
def teacher_with_id(teacher_id):
    """teacher main index: show teacher info, hypermedia"""
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
    # possiamo usarlo magari solo per l'hypermedia --> si meglio

    return build_response(res)


@app.route('/teacher/<int:teacher_id>/data/', methods=['GET', 'PUT'])
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
def teacher_class(teacher_id):
    '''show list of classes for the specific teacher'''
    session = create_session()
    teacher = session.query(Teacher).filter_by(id=teacher_id).first()
    # check if the teacher was found
    if not teacher:
        # OAuth should avoid this
        return build_response(None, error='Teacher id not found.'), 404
    # return response
    classes = teacher.classes
    cl = []

    for c in classes:
        cl.append({'id': c.id, 'name': c.name, 'room': c.room})

    res = {'class': cl}

    return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/')
def teacher_class_with_id(teacher_id, class_id):
    '''show class info for that teacher (students, subjects, timetable)'''
    session = create_session()
    c = session.query(Class).filter_by(id=class_id).first()
    subjects_list = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).all()

    if not c:
        return build_response(None, error='Class id not found.'), 404

    students = c.students
    st = []
    for s in students:
        st.append({'id': s.id, 'name': s.name, 'lastname': s.lastname})

    subjects = []
    for s in subjects_list:
        subjects.append({'id': s.id, 'name': s.name})

    res = {'class': {'id': class_id, 'name': c.name, 'room': c.room, 'students': st, 'subjects': subjects}}

    return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/')
def teacher_subject(teacher_id, class_id):
    '''show list of subject taught by a teacher in a class'''
    session = create_session()
    subjects_list = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).all()

    if not subjects_list:
        return build_response(None, error='Subjects not found.'), 404

    subjects = []
    for s in subjects_list:
        subjects.append({'id': s.id, 'name': s.name})

    res = {'subjects': subjects}

    return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/')
def teacher_subject_with_id(teacher_id, class_id, subject_id):
    '''show subject info taught by a teacher'''
    session = create_session()
    subject = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).filter_by(
        id=subject_id).first()
    if not subject:
        return build_response(None, error='Subject not found.'), 404

    res = {'id': subject.id, 'name': subject.name}

    return build_response(res)


# MA È UGUALE A CLASS DI TEACHER?
@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/')
def teacher_student(teacher_id, class_id, subject_id):
    '''show list of students for a subject taught by a teacher'''
    session = create_session()
    c = session.query(Class).filter_by(id=class_id).first()
    subject = session.query(Subject).filter_by(id=subject_id).filter_by(teacher_id=teacher_id).filter_by(
        class_id=class_id).first()

    if not c:
        return build_response(None, error='Class id not found.'), 404

    if not subject:
        return build_response(None, error='Subject id not found.'), 404

    students = c.students
    st = []
    for s in students:
        st.append({'id': s.id, 'name': s.name, 'lastname': s.lastname})

    # subjects = []
    # for s in subjects_list:
    #     subjects.append({'id': s.id, 'name': s.name})

    res = {'students': st}

    return build_response(res)

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/<int:student_id>/grade/', methods=['GET', 'POST', 'PUT'])
def teacher_student_grades(teacher_id, class_id, subject_id, student_id):
    session = create_session()
    if request.method == 'POST':
        '''add new grade'''

        try:
            data = request.get_json()
        except TypeError:
            return build_response(None, error='The request was not valid JSON.'), 400

        if 'date' not in data or 'value' not in data:
            return build_response(None, error='The JSON structure must contain all the requested parameters.'), 400

        date = data['date']
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
        pass
    else:
        '''show grades list'''
        # TODO check mi da errore con student_id=1,2 ma non con 3
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
def teacher_class_grades(teacher_id, class_id, subject_id):
    if request.method == 'POST':
        '''add new list of grades for the whole class'''
        pass
    else:
        '''show grades for the whole class for that subject'''
        pass

@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/timetable/')
def teacher_class_timetable(teacher_id, class_id):
    '''show timetable for that class'''
    # FIXME serve? informazioni complete vengono date da /class/
    pass

@app.route('/teacher/<int:teacher_id>/timetable/')
def teacher_timetable(teacher_id):
    '''show complete timetable for a teacher'''
    pass

@app.route('/teacher/<int:teacher_id>/appointment/')
def teacher_appointment(teacher_id):
    '''show list of appointments for a teacher'''
    pass

@app.route('/teacher/<int:teacher_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
def teacher_appointment_with_id(teacher_id, appointment_id):
    if request.method == 'PUT':
        '''edit appointment'''
        pass
    else:
        '''show appointment info'''
        pass

@app.route('/teacher/<int:teacher_id>/notifications/')
def teacher_notifications(teacher_id):
    '''show notifications for this teacher'''
    pass


'''PARENT'''

@app.route('/parent/', methods=['GET', 'POST'])
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
        # open db session
        session = create_session()
        # insert new teacher in db
        session.add(new_parent)
        session.commit()
        # return confirmation, new id
        new_id = new_parent.id
        return build_response({'id': new_id}), 201

    else:
        '''show list of parents'''
        # open db session
        session = create_session()
        parents = session.query(Parent).all()
        res = []
        for p in parents:
            res.append({'id': p.id, 'name': p.name, 'lastname': p.lastname})
        # return structured list
        return build_response(res)

@app.route('/parent/<int:parent_id>/')
def parent_with_id(parent_id):
    '''parent main index: parent info, hypermedia'''
    session = create_session()

    parent = session.query(Parent).filter_by(id=parent_id).first()

    if not parent:
        return build_response(None, error='Parent id not found'), 404
    res = {'name': parent.name,
           'lastname': parent.lastname}
    return build_response(res)


# todo standardizzare
@app.route('/parent/<int:parent_id>/data/', methods=['GET', 'PUT'])
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
def parent_child(parent_id):
    '''list children of parent'''
    pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/')
def parent_child_with_id(parent_id, student_id):
    '''show info of student?'''
    pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/data/', methods=['GET', 'PUT'])
def parent_child_data(parent_id, student_id):
    if request.method == 'PUT':
        '''edit child personal data'''
        pass
    else:
        '''show child personal data'''
        pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/grades/')
def parent_child_grades(parent_id, student_id):
    '''show all grades of the student'''
    pass

@app.route('/parent/<int:parent_id>/child/<int:student_id>/teachers/')
def parent_child_teacher(parent_id, student_id):
    '''list all child's teachers'''
    pass

@app.route('/parent/<int:parent_id>/appointment/', methods=['GET', 'POST'])
def parent_appointment(parent_id):
    if request.method == 'POST':
        '''create new appointment'''
        pass
    else:
        '''show all appointments'''
        pass
# TODO calendar-like support

@app.route('/parent/<int:parent_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
def parent_appointment_with_id(parent_id, appointment_id):
    if request.method == 'PUT':
        '''edit appointment'''
        pass
    else:
        '''show appointment info'''
        pass

@app.route('/parent/<int:parent_id>/payment/')
def parent_payment(parent_id):
    '''list all payments, paid or pending'''
    pass

@app.route('/parent/<int:parent_id>/payment/paid/')
def parent_payment_paid(parent_id):
    '''list old paid payments'''
    pass

@app.route('/parent/<int:parent_id>/payment/pending/')
def parent_payment_pending(parent_id):
    '''list pending payments'''
    pass

@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/')
def parent_payment_with_id(parent_id, payment_id):
    '''show payment info'''
    pass

@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/pay/', methods=['POST'])
def parent_pay(parent_id, payment_id):
    '''magic payment endpoint'''
    pass

@app.route('/parent/<int:parent_id>/notifications/')
def parent_notifications(parent_id):
    '''show notifications for this parent'''
    pass


'''ADMIN STUFF'''

@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        '''create new admin account'''
        pass
    else:
        '''list admin accounts'''
        pass

@app.route('/class/')
def classes():
    '''show list of classes'''
    '''POST create new classes non c'e' nelle specifiche'''
    pass

@app.route('/class/<int:class_id>/')
def class_with_id(class_id):
    '''show class info? non nelle specifiche'''
    pass

@app.route('/class/<int:class_id>/student/', methods=['GET', 'POST'])
def class_student(class_id):
    if request.method == 'POST':
        '''create new student'''
        pass
    else:
        '''show list of students in the class'''

@app.route('/student/')
def student():
    '''show list of students (non nelle specifiche)'''
    pass

@app.route('/student/<int:student_id>/')
def student_with_id(student_id):
    '''show student info (spostare in /class/student/?'''
    pass

@app.route('/payment/', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        '''create new payment for the whole school'''
        pass
    else:
        '''list school-wide payments'''
        pass

@app.route('/payment/parent/<int:parent_id>/', methods=['GET', 'POST'])
def payment_parent(parent_id):
    if request.method == 'POST':
        '''create new payment for a parent'''
        pass
    else:
        '''list payments for a parent'''
        pass

@app.route('/payment/class/<int:class_id>/', methods=['GET', 'POST'])
def payment_class(class_id):
    if request.method == 'POST':
        '''create new payment for a class'''
        pass
    else:
        '''list payments for a class'''
        pass

@app.route('/notification/', methods=['GET', 'POST'])
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
def notification_parent_with_id(parent_id):
    if request.method == 'POST':
        '''create parent notification'''
        pass
    else:
        '''list parent notifications'''
        pass

@app.route('/notification/teacher/', methods=['GET', 'POST'])
def notification_teachers():
    if request.method == 'POST':
        '''create notification to all teachers'''
        pass
    else:
        '''list notifications to all teachers'''
        pass

@app.route('/notification/teacher/<int:teacher_id>/', methods=['GET', 'POST'])
def notification_teacher_with_id(teacher_id):
    if request.method == 'POST':
        '''create notification for a teacher'''
        pass
    else:
        '''list a teacher's notifications'''
        pass

@app.route('/notification/class/<int:class_id>/', methods=['GET', 'POST'])
def notification_class(class_id):
    if request.method == 'POST':
        '''create class-wide notification'''
        pass
    else:
        '''list class-wide notifications'''
        pass

@app.route('/notification/class/<int:class_id>/parents/', methods=['GET', 'POST'])
def notification_class_parents(class_id):
    if request.method == 'POST':
        '''create a notification for the parents in a class'''
        pass
    else:
        '''list all notifications for the parents in a class'''
        pass

@app.route('/notification/class/<int:class_id>/teachers/', methods=['GET', 'POST'])
def notification_class_teachers(class_id):
    if request.method == 'POST':
        '''create a notification for the teachers in a class'''
        pass
    else:
        '''list all notifications for the teachers in a class'''
        pass

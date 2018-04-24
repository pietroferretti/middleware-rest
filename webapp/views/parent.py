# coding: utf-8

from flask import request, url_for

import json
import datetime
import calendar

from webapp import app
from webapp.utils import auth_check, build_link, build_response, check_appointment_time_constraint
from webapp.db.db_declarative import session
from webapp.db.db_declarative import Teacher, Parent, Student, Class, Subject, Appointment, Notification, Payment


@app.route('/parent/<int:parent_id>/')
@auth_check
def parent_with_id(parent_id):
    '''parent main index: parent info, hypermedia'''

    # hypermedia
    links = build_link('parent_with_id', parent_id=parent_id,
                       rel='self')
    links += build_link('parent_with_id', parent_id=parent_id,
                        rel='http://relations.highschool.com/index')

    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found', links=links), 404

    res = {'name': parent.name,
           'lastname': parent.lastname}

    # more hypermedia
    links += build_link('parent_data', parent_id=parent_id, rel='http://relations.highschool.com/data')
    links += build_link('parent_child', parent_id=parent_id, rel='http://relations.highschool.com/studentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/createappointment')
    links += build_link('parent_payment', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_notifications', parent_id=parent_id,
                        rel='http://relations.highschool.com/notificationlist')

    return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/data/', methods=['GET', 'PUT'])
@auth_check
def parent_data(parent_id):
    # hypermedia
    links = build_link('parent_data', parent_id=parent_id, rel='self')
    links += build_link('parent_data', parent_id=parent_id, rel='http://relations.highschool.com/data')
    links += build_link('parent_data', parent_id=parent_id, rel='http://relations.highschool.com/updatedata')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    if request.method == 'PUT':
        '''Edit parent personal data'''

        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        if 'name' in data:
            parent.name = data['name']

        if 'lastname' in data:
            parent.lastname = data['lastname']

        session.commit()

        return build_response({'data': {'name': parent.name, 'lastname': parent.lastname}}, links=links)

    else:
        '''Show parent personal data'''
        return build_response({'data': {'name': parent.name, 'lastname': parent.lastname}}, links=links)


@app.route('/parent/<int:parent_id>/child/')
@auth_check
def parent_child(parent_id):
    '''List children of this parent'''

    # hypermedia
    links = build_link('parent_child', parent_id=parent_id, rel='self')
    links += build_link('parent_child', parent_id=parent_id, rel='http://relations.highschool.com/studentlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    if not parent.children:
        return build_response(error='No students found.', links=links), 404

    children = []
    for c in parent.children:
        children.append({'name': c.name, 'lastname': c.lastname, 'id': c.id})
    res = {'students': children}
    # TODO perchè 10?
    # more hypermedia
    for i in range(min(10, len(children))):
        links += build_link('parent_child_with_id', parent_id=parent_id, student_id=children[i]['id'],
                            rel='http://relations.highschool.com/student')

    return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/child/<int:student_id>/')
@auth_check
def parent_child_with_id(parent_id, student_id):
    '''Show info for this student'''

    # hypermedia
    links = build_link('parent_child_with_id', parent_id=parent_id, student_id=student_id, rel='self')
    links += build_link('parent_child_with_id', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/student')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    student = session.query(Student).filter_by(parent_id=parent_id).filter_by(id=student_id).one()
    if not student:
        return build_response(error='Student not found.', links=links), 404

    # query
    c = session.query(Class).get(student.class_id)
    if c:
        subjects = []
        for s in c.subjects:
            subjects.append({'id': s.id, 'name': s.name})
        c_obj = {'id': c.id, 'name': c.name, 'room': c.room, 'subjects': subjects}
    else:
        c_obj = None

    res = {'student': {'name': student.name, 'lastname': student.lastname, 'id': student.id, 'class': c_obj}}

    # more hypermedia
    links += build_link('parent_child_data', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/data')
    links += build_link('parent_child_data', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/updatedata')
    links += build_link('parent_child_grades', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/gradelist')
    links += build_link('parent_child_teacher', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/teacherlist')

    return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/child/<int:student_id>/data/', methods=['GET', 'PUT'])
@auth_check
def parent_child_data(parent_id, student_id):
    # hypermedia
    links = build_link('parent_child_data', parent_id=parent_id, student_id=student_id,
                       rel='self')
    links += build_link('parent_child_data', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/data')
    links += build_link('parent_child_data', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/updatedata')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')
    links += build_link('parent_child', parent_id=parent_id, rel='http://relations.highschool.com/studentlist')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    student = session.query(Student).get(student_id)
    if not student or parent_id != student.parent_id:
        return build_response(error='Student not found.', links=links), 404

    if request.method == 'PUT':
        '''Edit child personal data'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        if 'name' in data:
            student.name = data['name']

        if 'lastname' in data:
            student.lastname = data['lastname']

        session.commit()

        res = {'data': {'name': student.name, 'lastname': student.lastname}}
        return build_response(res, links=links)

    else:
        '''Show child personal data'''

        res = {'data': {'name': student.name, 'lastname': student.lastname}}
        return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/child/<int:student_id>/grades/')
@auth_check
def parent_child_grades(parent_id, student_id):
    '''Show the student's grades'''

    # hypermedia
    links = build_link('parent_child_grades', parent_id=parent_id, student_id=student_id,
                       rel='self')
    links += build_link('parent_child_grades', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/gradelist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')
    links += build_link('parent_child', parent_id=parent_id, rel='http://relations.highschool.com/studentlist')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    student = session.query(Student).get(student_id)
    if not student or parent_id != student.parent_id:
        return build_response(error='Student not found.', links=links), 404

    # collect subject names
    subjects = session.query(Subject).all()
    subjects_names = {}
    for s in subjects:
        subjects_names[s.id] = s.name

    # query grades
    grades = []
    for g in student.grades:
        grades.append(
            {'grade': {'id': g.id, 'date': g.date, 'value': g.value, 'subject': subjects_names[g.subject_id]}})
    res = {'grades': grades}

    return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/child/<int:student_id>/teachers/')
@auth_check
def parent_child_teacher(parent_id, student_id):
    '''List the child's teachers'''

    # hypermedia
    links = build_link('parent_child_teacher', parent_id=parent_id, student_id=student_id,
                       rel='self')
    links += build_link('parent_child_teacher', parent_id=parent_id, student_id=student_id,
                        rel='http://relations.highschool.com/teacgherlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')
    links += build_link('parent_child', parent_id=parent_id, rel='http://relations.highschool.com/studentlist')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    student = session.query(Student).get(student_id)
    if not student or parent_id != student.parent_id:
        return build_response(error='Student not found.', links=links), 404

    # query
    c = session.query(Class).get(student.class_id)
    t_list = []
    if c:
        # get all teachers who have this class
        teachers = session.query(Teacher).all()
        for t in teachers:
            if c in t.classes:
                subjects = [s for s in t.subjects if s.class_id == student.class_id]
                s_list = []
                for s in subjects:
                    s_list.append({'id': s.id, 'name': s.name})
                t_list.append({'id': t.id, 'name': t.name, 'lastname': t.lastname, 'subjects': s_list})

    res = {'teachers': t_list}

    # more hypermedia
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/createappointment')

    return build_response(res, links=links)


def teacher_available(datetime_to_check, appointments, subjects):
    check_appointment = True

    app = [a for a in appointments if (a.date == datetime_to_check and a.teacher_accepted == 1)]
    if not app:
        i = datetime_to_check.hour
        for s in subjects:
            schedule = json.loads(s.timetable)
            for t in schedule:
                if t['day'] == datetime_to_check.weekday():
                    if t['start_hour'] <= i and t['end_hour'] > i:
                        return False
    return True


# TODO capire come vogliamo gestire gli errori, esempio id che non esiste del teacher
# TODO provare le post durante orario di lezione
# DONE hypermedia
@app.route('/parent/<int:parent_id>/appointment/', methods=['GET', 'POST'])
@auth_check
def parent_appointment(parent_id):

    # hypermedia
    links = build_link('parent_appointment', parent_id=parent_id, rel='self')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/createappointment')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    parent = session.query(Parent).get(parent_id)

    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    # more hypermedia
    ts = session.query(Teacher).all()
    for t in ts:
        if any(c.class_id in t.classes for c in parent.children):
            links += build_link('parent_appointment_month', parent_id=parent_id, teacher_id=t.id,
                                year=datetime.datetime.now().year, month=datetime.datetime.now().month,
                                rel='http://relations.highschool.com/freedays')
            links += build_link('parent_appointment_day', parent_id=parent_id, teacher_id=t.id,
                                year=datetime.datetime.now().year, month=datetime.datetime.now().month,
                                day=datetime.datetime.now().day, rel='http://relations.highschool.com/freeslots')

    if request.method == 'POST':
        '''Create new appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        if 'date' not in data or 'teacher_id' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        teacher = session.query(Teacher).filter_by(id=data['teacher_id']).one()

        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        new_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

        # check if teacher available


        if (check_appointment_time_constraint(new_date)):

            if (teacher_available(new_date, teacher.appointments, teacher.subjects)):
                new_appointment = Appointment(date=new_date, teacher_accepted=0, parent_accepted=1,
                                              teacher_id=data['teacher_id'], parent_id=parent_id)
                session.add(new_appointment)
                session.commit()
                a = new_appointment

                # more hypermedia
                links += build_link('parent_appointment_with_id', parent_id=parent_id, appointment_id=a.id,
                                    rel='http://relations.highschool.com/appointment')

                res = {'id': a.id, 'date': a.date, 'room': a.room, 'teacher accepted': a.teacher_accepted,
                                 'parent_accepted': a.parent_accepted,
                                 'teacher': {'id': a.teacher_id, 'name': teacher.name, 'lastname': teacher.lastname}}
                response = build_response(res, links=links)
                response.headers['Location'] = url_for('parent_appointment_with_id', parent_id=parent_id, appointment_id=a.id)
                return response, 201
            else:
                return build_response(error='Choose a free slot.', links=links), 400

        else:
            return build_response(error='Wrong date/time format.', links=links), 400


    else:
        '''Show all appointments'''
        appointments = []
        for a in parent.appointments:
            teacher = session.query(Teacher).filter_by(id=a.teacher_id).one()
            appointments.append({'id': a.id, 'date': a.date, 'room': a.room, 'teacher accepted': a.teacher_accepted,
                                 'parent_accepted': a.parent_accepted,
                                 'teacher': {'id': a.teacher_id, 'name': teacher.name, 'lastname': teacher.lastname}})

        # more hypermedia
        for i in range(min(10, len(appointments))):
            links += build_link('parent_appointment_with_id', parent_id=parent_id, appointment_id=appointments[i].id,
                            rel='http://relations.highschool.com/appointment')

        return build_response(appointments, links=links)


@app.route('/parent/<int:parent_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
@auth_check
def parent_appointment_with_id(parent_id, appointment_id):

    # hypermedia
    links = build_link('parent_appointment_with_id', parent_id=parent_id, appointment_id=appointment_id, rel='self')
    links += build_link('parent_appointment_with_id', parent_id=parent_id, appointment_id=appointment_id,
                        rel='http://relations.highschool.com/appointment')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/createappointment')


    appointment = session.query(Appointment).filter_by(id=appointment_id).filter_by(parent_id=parent_id).one()

    if not appointment:
        return build_response('Appointment not found.')

    if request.method == 'PUT':
        '''Edit appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        if 'date' in data:
            new_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

            if (check_appointment_time_constraint(new_date)):
                appointment.date = new_date
                appointment.parent_accepted = 0
            else:
                return build_response(error='Wrong date/time.', links=links), 400

        if 'teacher_id' in data:
            if int(data['teacher_id']) != appointment.teacher_id:
                appointment.teacher_accepted = 0
            appointment.teacher_id = int(data['teacher_id'])

        if 'parent_accepted' in data:
            appointment.parent_accepted = int(data['parent_accepted'])

        session.commit()

        teacher = session.query(Teacher).get(appointment.teacher_id)
        return build_response({'appointment': {'date': appointment.date, 'room': appointment.room,
                                               'teacher_accepted': appointment.teacher_accepted,
                                               'parent_accepted': appointment.parent_accepted,
                                               'teacher': {'name': teacher.name, 'lastname': teacher.lastname}}}, links=links)
    else:
        '''Show appointment info'''
        teacher = session.query(Teacher).filter_by(id=appointment.teacher_id).one()

        return build_response({'appointment': {'date': appointment.date, 'room': appointment.room,
                                               'teacher_accepted': appointment.teacher_accepted,
                                               'parent_accepted': appointment.parent_accepted,
                                               'teacher': {'name': teacher.name, 'lastname': teacher.lastname}}}, links=links)


# @app.route('/parent/<int:parent_id>/appointment/teacher/<int:teacher_id>/year/<int:year>/month/<int:month>/')
# @auth_check
# def parent_appointment_month(parent_id, teacher_id, year, month):
#     '''Show which days have appointments and free slots for the month'''
#     pass


# @app.route(
#     '/parent/<int:parent_id>/appointment/teacher/<int:teacher_id>/year/<int:year>/month/<int:month>/day/<int:day>/')
# @auth_check
# def parent_appointment_day(parent_id, teacher_id, year, month, day):
#     '''Show appointments, free slots for the day'''
#     pass

# day è tipo datetime


# TODO check caso falso
def available_slot_in_day(day_to_check, appointments, subjects):
    check_appointment = True

    app = [a for a in appointments if (
                a.date.year == day_to_check.year and a.date.month == day_to_check.month and a.date.day == day_to_check.day and a.teacher_accepted == 1)]
    for i in range(8, 13):
        for s in subjects:
            schedule = json.loads(s.timetable)
            for t in schedule:
                if t['day'] == day_to_check.weekday():
                    check_appointment = False
                    if t['start_hour'] < i or t['end_hour'] >= i:
                        for a in app:
                            if ((a.date.hour != i) or (a.date.hour == i and a.date.minute == 30)):
                                return True
            if check_appointment:
                if not app:
                    return True
                else:
                    for a in app:
                        if ((a.date.hour != i) or (a.date.hour == i and a.date.minute == 30)):
                            return True

    return False


@app.route('/parent/<int:parent_id>/appointment/teacher/<int:teacher_id>/year/<int:year>/month/<int:month>/')
@auth_check
def parent_appointment_month(parent_id, teacher_id, year, month):
    '''Show which days have appointments and free slots for the month'''

    # hypermedia
    links = build_link('parent_appointment_month', parent_id=parent_id, teacher_id=teacher_id,
                        year=year, month=month, rel='self')
    links += build_link('parent_appointment_month', parent_id=parent_id, teacher_id=teacher_id,
                        year=year, month=month, rel='http://relations.highschool.com/freedays')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/createappointment')

    teacher = session.query(Teacher).get(teacher_id)

    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    res = []
    for d in calendar.Calendar().itermonthdays(year, month):
        if d >= datetime.date.today().day and available_slot_in_day(datetime.datetime(year, month, d),
                                                                    teacher.appointments, teacher.subjects):
            res.append({'date': datetime.datetime(year, month, d)})
    if not res:
        return build_response(error='No available appointments for this month.', links=links), 404

    # more hypermedia
    for d in res:
        links += build_link('parent_appointment_day', parent_id=parent_id, teacher_id=teacher_id,
                            year=year, month=month,
                            day=d['date'].day, rel='http://relations.highschool.com/freeslots')

    # day_to_check = datetime.datetime(year,month,3)
    # app = [a for a in teacher.appointments if (a.date.year == day_to_check.year and a.date.month == day_to_check.month and a.date.day == day_to_check.day and a.teacher_accepted == 1)]

    return build_response({'available_days': res})

@app.route(
    '/parent/<int:parent_id>/appointment/teacher/<int:teacher_id>/year/<int:year>/month/<int:month>/day/<int:day>/')
@auth_check
def parent_appointment_day(parent_id, teacher_id, year, month, day):
    '''Show appointments, free slots for the day'''

    # hypermedia
    links = build_link('parent_appointment_day', parent_id=parent_id, teacher_id=teacher_id,
                        year=year, month=month, day=day, rel='self')
    links += build_link('parent_appointment_day', parent_id=parent_id, teacher_id=teacher_id,
                        year=year, month=month, day=day, rel='http://relations.highschool.com/freeslots')
    links += build_link('parent_appointment_month', parent_id=parent_id, teacher_id=teacher_id,
                        year=year, month=month, rel='http://relations.highschool.com/freedays')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('parent_appointment', parent_id=parent_id,
                        rel='http://relations.highschool.com/createappointment')

    teacher = session.query(Teacher).get(teacher_id)

    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    # setto tutti gli slot a 1=libero
    daily_slots = {}
    for i in range(8, 13):
        daily_slots[str(i) + '00'] = 1
        daily_slots[str(i) + '30'] = 1

    for a in teacher.appointments:
        if (a.date.year == year and a.date.month == month and a.date.day == day and a.teacher_accepted == 1):
            daily_slots[str(a.date.hour) + str(a.date.minute)] = 0

    w_day = datetime.datetime(year, month, day).weekday()

    for s in teacher.subjects:
        schedule = json.loads(s.timetable)
        for t in schedule:
            if t['day'] == w_day:
                for x in range(t['start_hour'], t['end_hour']):
                    # setto 2 slot come occupati -> lezioni vanno di ora in ora
                    daily_slots[str(x) + '00'] = 0
                    daily_slots[str(x) + '30'] = 0

    free = []
    for key, value in daily_slots.items():
        if value == 1:
            free.append(key)

    res = {'date': datetime.datetime(year, month, day), 'free_slots': free}

    return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/payment/')
@auth_check
def parent_payment(parent_id):
    '''List all payments, paid or pending'''

    # hypermedia
    links = build_link('parent_payment', parent_id=parent_id, rel='self')
    links += build_link('parent_payment', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_payment_paid', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_payment_pending', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    parent = session.query(Parent).get(parent_id)

    if not parent:
        return build_response('Parent not found.', links=links), 404

    payments = []

    for p in parent.payments:
        payments.append({'id': p.id, 'amount': p.amount, 'date': p.date, 'reason': p.reason, 'pending': p.is_pending})

    # more hypermedia
    for i in range(min(5, len(parent.payments))):
        links += build_link('parent_payment_with_id', parent_id=parent_id, payment_id=payments[i].payment_id,
                            rel='http://relations.highschool.com/payment')

    return build_response({'payments': payments}, links=links)


@app.route('/parent/<int:parent_id>/payment/paid/')
@auth_check
def parent_payment_paid(parent_id):
    '''list old paid payments'''

    # hypermedia
    links = build_link('parent_payment_paid', parent_id=parent_id, rel='self')
    links += build_link('parent_payment_paid', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_payment', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_payment_pending', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')


    # checks
    parent = session.query(Parent).get(parent_id)

    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    payments = []

    for p in parent.payments:
        if (not p.is_pending):
            payments.append({'id': p.id, 'amount': p.amount, 'date': p.date, 'reason': p.reason})

    # more hypermedia
    for i in range(min(5, len(parent.payments))):
        links += build_link('parent_payment_with_id', parent_id=parent_id, payment_id=payments[i].payment_id,
                            rel='http://relations.highschool.com/payment')

    return build_response({'payments': payments}, links=links)


@app.route('/parent/<int:parent_id>/payment/pending/')
@auth_check
def parent_payment_pending(parent_id):
    '''list pending payments'''

    # hypermedia
    links = build_link('parent_payment_pending', parent_id=parent_id, rel='self')
    links += build_link('parent_payment_pending', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_payment', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_payment_paid', parent_id=parent_id,
                        rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    parent = session.query(Parent).get(parent_id)

    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    payments = []

    for p in parent.payments:
        if (p.is_pending):
            payments.append({'id': p.id, 'amount': p.amount, 'date': p.date, 'reason': p.reason})

    # more hypermedia
    for i in range(min(5, len(parent.payments))):
        links += build_link('parent_payment_with_id', parent_id=parent_id, payment_id=payments[i].payment_id,
                            rel='http://relations.highschool.com/payment')

    return build_response({'payments': payments}, links=links)


@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/')
@auth_check
def parent_payment_with_id(parent_id, payment_id):
    '''show payment info'''

    # hypermedia
    links = build_link('parent_payment_with_id', parent_id=parent_id, payment_id=payment_id, rel='self')
    links += build_link('parent_payment_with_id', parent_id=parent_id, payment_id=payment_id,
                       rel='http://relation.highschool.com/payment')
    links += build_link('parent_payment', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    payment = session.query(Payment).get(payment_id)

    if not payment or payment.parent_id != parent_id:
        return build_response(error='Payment not found.', links=links), 404

    res = {'amount': payment.amount, 'date': payment.date, 'reason': payment.reason, 'pending': payment.is_pending}

    # more hypermedia
    if payment.is_pending:
        links += build_link('parent_pay', parent_id=parent_id, payment_id=payment_id,
                            rel='http://relations.highschool.com/completepayment')

    return build_response(res, links=links)


@app.route('/parent/<int:parent_id>/payment/<int:payment_id>/pay/', methods=['PUT'])
@auth_check
def parent_pay(parent_id, payment_id):
    '''Magic payment endpoint'''
    # TODO test

    # hypermedia
    links = build_link('parent_pay', parent_id=parent_id, payment_id=payment_id, rel='self')
    links = build_link('parent_pay', parent_id=parent_id, payment_id=payment_id,
                       rel='http://relations.highschool.com/completepayment')
    links += build_link('parent_payment', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    payment = session.query(Payment).get(payment_id)
    if not payment or payment.parent_id != parent_id:
        return build_response(error='Payment not found.', links=links), 404

    if payment.is_pending:
        # MAGIC HAPPENS!
        payment.is_pending = False
        session.commit()
        return build_response('Payment confirmed.', links=links)


@app.route('/parent/<int:parent_id>/notifications/')
@auth_check
def parent_notifications(parent_id):
    '''Show notifications for this parent'''

    # hypermedia
    links = build_link('parent_notifications', parent_id=parent_id, rel='self')
    links += build_link('parent_notifications', parent_id=parent_id,
                        rel='http://relations.highschool.com/notificationlist')
    links += build_link('parent_with_id', parent_id=parent_id, rel='http://relations.highschool.com/index')

    # checks
    parent = session.query(Parent).get(parent_id)
    if not parent:
        return build_response(error='Parent not found.', links=links), 404

    # query
    notifications_all = session.query(Notification).filter_by(scope='all').all()
    notifications_teachers = session.query(Notification).filter_by(scope='parents').all()
    notifications_one_parent = session.query(Notification).filter_by(scope='one_parent').filter_by(
        parent_id=parent_id).all()

    children_not_list = []

    for c in parent.children:
        notifications_class_parent = session.query(Notification).filter_by(class_id=c.class_id).all()

        child_not_list = []
        for n in notifications_class_parent:
            child_not_list.append({'date': n.date, 'text': n.text, 'class_notification_scope': n.scope})

        children_not_list.append(
            {'student': {'name': c.name, 'lastname': c.lastname}, 'notifications': child_not_list})

    notifications_teachers_list = []
    for n in notifications_teachers:
        notifications_teachers_list.append({'date': n.date, 'text': n.text})

    notifications_all_list = []
    for n in notifications_all:
        notifications_all_list.append({'date': n.date, 'text': n.text})

    notifications_one_parent_list = []
    for n in notifications_one_parent:
        notifications_one_parent_list.append({'date': n.date, 'text': n.text})

    return build_response([{'scope': 'class', 'notifications': children_not_list},
                           {'scope': 'parents', 'notifications': notifications_teachers_list},
                           {'scope': 'all', 'notifications': notifications_all_list},
                           {'scope': 'one_parent', 'notifications': notifications_one_parent_list}], links=links)


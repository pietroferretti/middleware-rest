# coding: utf-8

from flask import request, url_for

import json
import datetime

from webapp import app
from webapp.utils import auth_check, build_link, build_response, check_appointment_time_constraint
from webapp.db.db_declarative import session, Teacher, Parent, Student, Class, Subject, Grade, Appointment, Notification

from sqlalchemy.orm.exc import NoResultFound


@app.route('/teacher/<int:teacher_id>/')
@auth_check
def teacher_with_id(teacher_id):
    '''Teacher main index: show teacher info, hypermedia'''

    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id,
                       rel='self')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')

    # get teacher with id
    teacher = session.query(Teacher).get(teacher_id)

    # check if the teacher was found
    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    # return response object
    res = {'teacher': {'id': teacher_id, 'name': teacher.name, 'lastname': teacher.lastname}}

    # more hypermedia
    links += build_link('teacher_data', teacher_id=teacher_id,
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
    links += build_link('teacher_appointment', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/createappointment')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/data/', methods=['GET', 'PUT'])
@auth_check
def teacher_data(teacher_id):
    # hypermedia
    links = build_link('teacher_data', teacher_id=teacher_id,
                       rel='self')
    links += build_link('teacher_data', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/data')
    links += build_link('teacher_data', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/updatedata')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')

    if request.method == 'PUT':
        '''Modify teacher personal data'''

        # check content type
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        # check json content
        if 'name' not in data and 'lastname' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        # update teacher with query
        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.'), 404

        if 'name' in data:
            teacher.name = data['name']
        if 'lastname' in data:
            teacher.lastname = data['lastname']
        session.commit()

        res = {'data': {'name': teacher.name,
               'lastname': teacher.lastname}}

        # return build_response(res, links=links)

    else:
        '''Show teacher personal data'''
        # get data from teachers with id
        teacher = session.query(Teacher).get(teacher_id)
        # check if the teacher was found
        if not teacher:
            return build_response(error='Teacher not found.'), 404

        res = {'data': {'name': teacher.name,
               'lastname': teacher.lastname}}

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/')
@auth_check
def teacher_class(teacher_id):
    '''List classes for this teacher'''

    # hypermedia
    links = build_link('teacher_class', teacher_id=teacher_id,
                       rel='self')
    links += build_link('teacher_class', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/classlist')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')

    teacher = session.query(Teacher).get(teacher_id)

    # check if the teacher was found
    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    # return response
    classes = teacher.classes
    cl = []
    for c in classes:
        cl.append({'id': c.id, 'name': c.name, 'room': c.room})
    res = {'classes': cl}

    # more hypermedia
    for i in range(min(10, len(cl))):
        links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=cl[i]['id'],
                            rel='http://relations.highschool.com/class')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/')
@auth_check
def teacher_class_with_id(teacher_id, class_id):
    '''Show some class info for this teacher, with hypermedia to students, subjects, timetable'''

    # hypermedia
    links = build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=class_id,
                       rel='self')
    links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/class')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_class', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/classlist')

    # checks
    teacher = session.query(Teacher).get(teacher_id)
    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    c = session.query(Class).get(class_id)
    if not c:
        return build_response(error='Class not found.', links=links), 404

    res = {'class': {'id': class_id, 'name': c.name, 'room': c.room}}

    # more hypermedia
    links += build_link('teacher_class_timetable', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/timetable')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/subjectlist')
    links += build_link('teacher_student', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/studentlist')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/student/')
@auth_check
def teacher_student(teacher_id, class_id):
    '''Show list of students for this class'''

    # hypermedia
    links = build_link('teacher_student', teacher_id=teacher_id, class_id=class_id,
                       rel='self')
    links += build_link('teacher_student', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/studentlist')
    links += build_link('teacher_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/index')
    links += build_link('teacher_class_with_id', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/class')

    # checks
    teacher = session.query(Teacher).get(teacher_id)
    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    c = session.query(Class).get(class_id)
    if not c:
        return build_response(error='Class not found.', links=links), 404

    # query
    students = c.students
    if not students:
        return build_response(error='No students found.', links=links), 404

    st = []
    for s in students:
        st.append({'id': s.id, 'name': s.name, 'lastname': s.lastname})

    # response object
    res = {'students': st}

    # more hypermedia
    for i in range(min(10, len(students))):
        links += build_link('teacher_student_grades', teacher_id=teacher_id, class_id=class_id,
                            student_id=students[i].id, rel='http://relations.highschool.com/gradelist')
        links += build_link('teacher_student_grades', teacher_id=teacher_id, class_id=class_id,
                            student_id=students[i].id, rel='http://relations.highschool.com/publishgrade')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/')
@auth_check
def teacher_subject(teacher_id, class_id):
    '''Show list of subjects taught by a teacher in a class'''

    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id,
                       rel='http://relations.highschool.com/index')
    links += build_link('teacher_class', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/class')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/subjectlist')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='self')

    teacher = session.query(Teacher).get(teacher_id)
    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    c = session.query(Class).get(class_id)
    if not c or not c in teacher.classes:
        return build_response(error='Class not found.', links=links), 404

    subjects_list = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).all()
    if not subjects_list:
        return build_response(error='Subjects not found.', links=links), 404

    subjects = []
    for s in subjects_list:
        subjects.append({'id': s.id, 'name': s.name})

    res = {'subjects': subjects}

    # more hypermedia
    for i in range(min(10, len(subjects))):
        links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id,
                            subject_id=subjects[i]['id'],
                            rel='http://relations.highschool.com/subject')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/')
@auth_check
def teacher_subject_with_id(teacher_id, class_id, subject_id):
    '''Show info on this subject taught by a teacher'''

    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id,
                       rel='http://relations.highschool.com/index')
    links += build_link('teacher_subject', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/subjectlist')
    links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/subject')
    links += build_link('teacher_subject_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='self')

    teacher = session.query(Teacher).get(teacher_id)
    if not teacher:
        return build_response(error='Teacher not found.', links=links), 404

    c = session.query(Class).get(class_id)
    if not c or not c in teacher.classes:
        return build_response(error='Class not found.', links=links), 404

    subject = session.query(Subject).get(subject_id)
    if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
        return build_response(error='Subject not found.', links=links), 404

    res = {'subject': {'id': subject.id, 'name': subject.name}}

    # more hypermedia
    links += build_link('teacher_student', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/studentlist')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/gradelist')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/publishgrade')

    return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/student/<int:student_id>/grade/',
           methods=['GET', 'POST'])
@auth_check
def teacher_student_grades(teacher_id, class_id, subject_id, student_id):
    # hypermedia
    links = build_link('teacher_student_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       student_id=student_id, rel='self')
    links += build_link('teacher_student_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        student_id=student_id, rel='http://relations.highschool.com/gradelist')
    links += build_link('teacher_student_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        student_id=student_id, rel='http://relations.highschool.com/publishgrade')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')

    if request.method == 'POST':
        '''Add new grade for this student'''

        # checks
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.'), 400

        if 'date' not in data or 'value' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.'), 400

        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        student = session.query(Student).get(student_id)
        if not student or student.class_id != class_id:
            return build_response(error='Student not found.', links=links), 404

        # create new grade
        date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
        value = data['value']

        new_grade = Grade(date=date, subject_id=subject_id, student_id=student_id, value=value)

        session.add(new_grade)
        session.commit()

        # create response object
        new_id = new_grade.id
        g_obj = {'id': new_id, 'date': str(date), 'subject_id': subject_id, 'student_id': student_id, 'value': value}
        res = {'grade': g_obj}

        # more hypermedia
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                   grade_id=new_id, rel='http://relations.highschool.com/grade')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                   grade_id=new_id, rel='http://relations.highschool.com/updategrade')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                   grade_id=new_id, rel='http://relations.highschool.com/deletegrade')

        response = build_response(res, links=links)
        response.headers['Location'] = url_for('teacher_grade_with_id',  teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                   grade_id=new_id)
        return response, 201

    else:
        '''Show list of grades for this student'''

        # checks
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.', links=links), 400

        if 'date' not in data or 'value' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        student = session.query(Student).get(student_id)
        if not student or student.class_id != class_id:
            return build_response(error='Student not found.', links=links), 404

        # query
        grade_list = session.query(Grade).filter_by(subject_id=subject_id).filter_by(student_id=student_id).all()

        if not grade_list:
            return build_response(error='Grades not found.'), 404

        grades = []
        for g in grade_list:
            grades.append({'id': g.id, 'date': g.date, 'value': g.value})

        res = {'grades': grades}

        # more hypermedia
        for i in range(min(10, len(grade_list))):
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       grade_id=grades[i].id, rel='http://relations.highschool.com/grade')
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       grade_id=grades[i].id, rel='http://relations.highschool.com/updategrade')
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       grade_id=grades[i].id, rel='http://relations.highschool.com/deletegrade')

        return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<subject_id>/grade/', methods=['GET', 'POST'])
@auth_check
def teacher_class_grades(teacher_id, class_id, subject_id):

    # hypermedia
    links = build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       rel='self')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/gradelist')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/publishgrade')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')

    if request.method == 'POST':
        '''Add new list of grades for the whole class'''

        # checks
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.'), 400

        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        if 'grades' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.'), 400

        g_list = []
        for grade in data['grades']:
            try:
                date = datetime.datetime.strptime(grade['date'], '%Y-%m-%d %H:%M')
                value = grade['value']
                student_id = grade['student_id']
            except KeyError:
                return build_response(error='The JSON structure must contain all the requested parameters.'), 400

            try:
                check_student_class = session.query(Student).filter_by(id=student_id).filter_by(class_id=class_id).one()
            except NoResultFound:
                session.rollback()
                return build_response(grade, error='Student not in this class.'), 404

            new_grade = Grade(date=date, subject_id=subject_id, student_id=student_id, value=value)
            session.add(new_grade)
            g_list.append({'id': new_grade.id, 'date': str(date), 'subject_id': subject_id, 'student_id': student_id,
                           'value': value})

        session.commit()

        # response object
        res = {'grades': g_list}

        # more hypermedia
        for g in g_list:
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       grade_id=g['id'], rel='http://relations.highschool.com/grade')
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       grade_id=g['id'], rel='http://relations.highschool.com/updategrade')
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                       grade_id=g['id'], rel='http://relations.highschool.com/deletegrade')

        return build_response(res, links=links), 201

    else:
        '''Show grades for the whole class for this subject'''

        # checks
        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        student_list = session.query(Student).filter_by(class_id=class_id).all()

        if not student_list:
            return build_response(error='Students not found.', links=links), 404

        st = []
        all_grades = []
        for s in student_list:
            grades_list = []
            for g in s.grades:
                if g.subject_id == subject_id:
                    grades_list.append({'id': g.id, 'date': g.date, 'value': g.value, 'subject_id': g.subject_id})
            st.append({'id': s.id, 'name': s.name, 'lastname': s.lastname, 'grades': grades_list})
            all_grades += grades_list

        res = {'students': st}

        # more hypermedia
        for i in range(min(10, len(all_grades))):
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                                grade_id=all_grades[i]['id'], rel='http://relations.highschool.com/grade')
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                                grade_id=all_grades[i]['id'], rel='http://relations.highschool.com/updategrade')
            links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                                grade_id=all_grades[i]['id'], rel='http://relations.highschool.com/deletegrade')

        return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/subject/<int:subject_id>/grade/<int:grade_id>/',
           methods=['GET', 'PUT', 'DELETE'])
@auth_check
def teacher_grade_with_id(teacher_id, class_id, subject_id, grade_id):
    # hypermedia
    links = build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/gradelist')
    links += build_link('teacher_class_grades', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                        rel='http://relations.highschool.com/publishgrade')

    if request.method == 'PUT':
        '''Edit old grade'''

        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                           grade_id=grade_id, rel='self')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            grade_id=grade_id, rel='http://relations.highschool.com/grade')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            grade_id=grade_id, rel='http://relations.highschool.com/updategrade')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            grade_id=grade_id, rel='http://relations.highschool.com/deletegrade')

        # checks
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.'), 400

        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        grade = session.query(Grade).get(grade_id)

        if not grade:
            return build_response(error='Grade not found.', links=links), 404

        # update
        if 'date' in data:
            grade.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

        if 'value' in data:
            grade.value = int(data['value'])

        session.commit()

        # response
        g_obj = {'id': grade.id, 'date': str(grade.date), 'value': grade.value, 'student_id': grade.student_id,
                 'subject_id': grade.subject_id}
        res = {'grade': g_obj}

        return build_response(res, links=links)

    elif request.method == 'GET':
        '''Show grade'''

        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                           grade_id=grade_id, rel='self')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            grade_id=grade_id, rel='http://relations.highschool.com/grade')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            grade_id=grade_id, rel='http://relations.highschool.com/updategrade')
        links += build_link('teacher_grade_with_id', teacher_id=teacher_id, class_id=class_id, subject_id=subject_id,
                            grade_id=grade_id, rel='http://relations.highschool.com/deletegrade')

        # checks
        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        grade = session.query(Grade).get(grade_id)

        if not grade:
            return build_response(error='Grade not found.', links=links), 404

        g_obj = {'id': grade.id, 'date': str(grade.date), 'value': grade.value, 'student_id': grade.student_id,
                 'subject_id': grade.subject_id}
        res = {'grade': g_obj}

        return build_response(res, links=links)

    elif request.method == 'DELETE':
        '''Delete grade'''

        # checks
        teacher = session.query(Teacher).get(teacher_id)
        if not teacher:
            return build_response(error='Teacher not found.', links=links), 404

        c = session.query(Class).get(class_id)
        if not c or not c in teacher.classes:
            return build_response(error='Class not found.', links=links), 404

        subject = session.query(Subject).get(subject_id)
        if not subject or teacher_id != subject.teacher_id or class_id != subject.class_id:
            return build_response(error='Subject not found.', links=links), 404

        grade = session.query(Grade).get(grade_id)

        if not grade:
            return build_response(error='Grade not found.', links=links), 404

        # delete object
        session.delete(grade)
        session.commit()

        res = {'message': 'Grade deleted successfully.'}

        return build_response(res, links=links)


@app.route('/teacher/<int:teacher_id>/class/<int:class_id>/timetable/')
@auth_check
def teacher_class_timetable(teacher_id, class_id):
    '''Show timetable for that class'''

    # hypermedia
    links = build_link('teacher_class_timetable', teacher_id=teacher_id, class_id=class_id, rel='self')
    links += build_link('teacher_class_timetable', teacher_id=teacher_id, class_id=class_id,
                        rel='http://relations.highschool.com/timetable')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')
    links += build_link('teacher_timetable', teacher_id=teacher_id, rel='http://relations.highschool.com/timetable')

    subjects = session.query(Subject).filter_by(teacher_id=teacher_id).filter_by(class_id=class_id).all()

    if not subjects:
        return build_response('Data not found.', links=links), 404

    timetable = []
    for s in subjects:
        c = session.query(Class).get(s.class_id)
        timetable.append({'subjects_name': s.name, 'schedule': json.loads(s.timetable)})

    return build_response(timetable, links=links)


@app.route('/teacher/<int:teacher_id>/timetable/')
@auth_check
def teacher_timetable(teacher_id):
    '''Show complete timetable for a teacher'''

    # hypermedia
    links = build_link('teacher_timetable', teacher_id=teacher_id, rel='self')
    links += build_link('teacher_timetable', teacher_id=teacher_id, rel='http://relations.highschool.com/timetable')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')

    teacher = session.query(Teacher).get(teacher_id)

    if not teacher:
        return build_response('Teacher not found.', links=links), 404

    # query
    timetable = []
    classes_id = set()
    for s in teacher.subjects:
        c = session.query(Class).get(s.class_id)
        timetable.append(
            {'subjects_name': s.name, 'schedule': json.loads(s.timetable),
             'class': {'name': c.name, 'id': c.id, 'room': c.room}})
        classes_id.add(c.id)

    # more hypermedia
    for c in classes_id:
        links += build_link('teacher_class_timetable', teacher_id=teacher_id, class_id=c,
                            rel='http://relations.highschool.com/timetable')
    # response
    return build_response({'timetable': timetable}, links=links)


@app.route('/teacher/<int:teacher_id>/appointment/', methods=['GET', 'POST'])
@auth_check
def teacher_appointment(teacher_id):
    # hypermedia
    links = build_link('teacher_appointment', teacher_id=teacher_id, rel='self')
    links += build_link('teacher_appointment', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/appointmentlist')
    links += build_link('teacher_appointment', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/createappointment')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')

    if request.method == 'POST':
        '''create new appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.'), 400

        if 'date' not in data or 'parent_id' not in data or 'room' not in data:
            return build_response(error='The JSON structure must contain all the requested parameters.',
                                  links=links), 400

        new_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

        if (check_appointment_time_constraint(new_date)):
            new_appointment = Appointment(date=new_date, teacher_accepted=1, parent_accepted=0, teacher_id=teacher_id,
                                          room=data['room'], parent_id=data['parent_id'])
            session.add(new_appointment)
            session.commit()
            a = new_appointment
            parent = session.query(Parent).get(data['parent_id'])
            res = {'appointment': {'id': a.id, 'date': a.date, 'room': a.room,
                                   'parent_accepted': a.parent_accepted,
                                   'teacher_accepted': a.teacher_accepted,
                                   'parent': {'id': parent.id, 'name': parent.name, 'lastname': parent.lastname}}}

            # more hypermedia
            links += build_link('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=a.id,
                                rel='http://www.highschool.com/appointment')
            response = build_response(res, links=links)
            response.headers['Location'] = url_for('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=a.id)
            return response, 201

        else:
            return build_response(error='Wrong date/time.', links=links), 400

    '''Show list of appointments for a teacher'''

    appointments_list = session.query(Appointment).filter_by(teacher_id=teacher_id).all()

    if not appointments_list:
        return build_response(error='Appointments not found.', links=links), 404

    appointments = []
    for a in appointments_list:
        parent = session.query(Parent).filter_by(id=a.parent_id).one()
        appointments.append({'appointment': {'id': a.id, 'date': a.date, 'room': a.room,
                                             'parent_accepted': a.parent_accepted,
                                             'teacher_accepted': a.teacher_accepted,
                                             'parent': {'id': parent.id, 'name': parent.name,
                                                        'lastname': parent.lastname}}})
        links += build_link('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=a.id,
                            rel='http://relations.highschool.com/appointment')
        links += build_link('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=a.id,
                            rel='http://relations.highschool.com/updateappointment')

    return build_response(appointments, links=links)


@app.route('/teacher/<int:teacher_id>/appointment/<int:appointment_id>/', methods=['GET', 'PUT'])
@auth_check
def teacher_appointment_with_id(teacher_id, appointment_id):
    # hypermedia
    links = build_link('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=appointment_id, rel='self')
    links += build_link('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=appointment_id,
                        rel='http://relations.highschool.com/appointment')
    links += build_link('teacher_appointment_with_id', teacher_id=teacher_id, appointment_id=appointment_id,
                        rel='http://relations.highschool.com/updateappointment')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')
    links += build_link('teacher_appointment', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/appointmentlist')

    appointment = session.query(Appointment).filter_by(id=appointment_id).filter_by(teacher_id=teacher_id).one()

    if not appointment:
        return build_response(error='Appointment not found.'), 404

    if request.method == 'PUT':
        '''Edit appointment'''
        try:
            data = request.get_json()
        except TypeError:
            return build_response(error='The request was not valid JSON.'), 400

        if 'date' in data:
            new_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')

            if (check_appointment_time_constraint(new_date)):
                appointment.date = new_date
                appointment.parent_accepted = 0
            else:
                return build_response(error='Wrong date/time.'), 400

        if 'room' in data:
            appointment.room = data['room']

        if 'parent_id' in data:
            if int(data['parent_id']) != appointment.parent_id:
                appointment.parent_accepted = 0
            appointment.parent_id = int(data['parent_id'])

        if 'teacher_accepted' in data:
            appointment.teacher_accepted = int(data['teacher_accepted'])

        session.commit()

        parent = session.query(Parent).get(data['parent_id'])

        return build_response({'appointment': {'date': appointment.date, 'room': appointment.room,
                                               'teacher_accepted': appointment.teacher_accepted,
                                               'parent_accepted': appointment.parent_accepted,
                                               'parent': {'id': parent.id, 'name': parent.name,
                                                          'lastname': parent.lastname}}}, links=links)

    else:
        '''Show appointment info'''
        parent = session.query(Parent).filter_by(id=appointment.parent_id).one()

        return build_response({'appointment': {'date': appointment.date, 'room': appointment.room,
                                               'teacher_accepted': appointment.teacher_accepted,
                                               'parent_accepted': appointment.parent_accepted,
                                               'parent': {'id': parent.id, 'name': parent.name,
                                                          'lastname': parent.lastname}}}, links=links)


@app.route('/teacher/<int:teacher_id>/notifications/')
@auth_check
def teacher_notifications(teacher_id):
    '''Show notifications for this teacher'''

    # hypermedia
    links = build_link('teacher_appointment_with_id', teacher_id=teacher_id, rel='self')
    links += build_link('teacher_appointment_with_id', teacher_id=teacher_id,
                        rel='http://relations.highschool.com/notificationlist')
    links += build_link('teacher_with_id', teacher_id=teacher_id, rel='http://relations.highschool.com/index')

    # checks
    teacher = session.query(Teacher).filter_by(id=teacher_id).one()

    if not teacher:
        return build_response(error='Teacher not found.', links=links)

    # query
    notifications_all = session.query(Notification).filter_by(scope='all').all()
    notifications_teachers = session.query(Notification).filter_by(scope='teachers').all()
    notifications_one_teacher = session.query(Notification).filter_by(scope='one_teacher').filter_by(
        teacher_id=teacher_id).all()

    classes_not_list = []
    for c in teacher.classes:

        notifications_class = session.query(Notification).filter_by(class_id=c.id).all()

        class_not_list = []
        for n in notifications_class:
            class_not_list.append({'date': n.date, 'text': n.text, 'class_notification_scope': n.scope})

        classes_not_list.append(
            {'class': {'id': c.id, 'name': c.name}, 'notifications': class_not_list})

    notifications_teachers_list = []
    for n in notifications_teachers:
        notifications_teachers_list.append({'date': n.date, 'text': n.text})

    notifications_all_list = []
    for n in notifications_all:
        notifications_all_list.append({'date': n.date, 'text': n.text})

    notifications_one_teacher_list = []
    for n in notifications_one_teacher:
        notifications_one_teacher_list.append({'date': n.date, 'text': n.text})

    return build_response([{'scope': 'class', 'notifications': classes_not_list},
                           {'scope': 'teachers', 'notifications': notifications_teachers_list},
                           {'scope': 'all', 'notifications': notifications_all_list},
                           {'scope': 'one_teacher', 'notifications': notifications_one_teacher_list}], links=links)


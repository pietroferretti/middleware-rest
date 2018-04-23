# coding: utf-8

from flask import request, url_for

import hashlib
import datetime
import os

from webapp import app
from webapp.utils import auth_check, build_link, build_response
from webapp.db.db_declarative import session
from webapp.db.db_declarative import Teacher, Parent, Student, Class, Notification, Payment, Account



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

        return build_response(links=links)


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
        links += build_link('admin_teacher_with_id', teacher_id=new_teacher.id, rel='http://relations.highschool.com/teacher')

        response = build_response(res, links=links)
        response.headers['Location'] = url_for('admin_teacher_with_id', teacher_id=new_teacher.id)
        return response, 201

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

    return build_response(res, links=links)


@app.route('/admin/parent/', methods=['GET', 'POST'])
@auth_check
def admin_parent():
    # hypermedia
    links = build_link('admin_parent', rel='self')
    links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
    links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
    links += build_link('admin', rel='http://relations.highschool.com/index')

    if request.method == 'POST':
        '''Create new parent account'''

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
        links += build_link('admin_parent_with_id', parent_id=new_parent.id, rel='http://relations.highschool.com/parent')

        response = build_response(res, links=links)
        response.headers['Location'] = url_for('admin_parent_with_id', parent_id=new_parent.id)
        return response, 201

    else:
        '''Show list of parents'''

        # get list of parents from db
        parents = session.query(Parent).all()

        # check query result
        if not parents:
            return build_response(error='No parents found.', links=links), 404

        # build response
        p_list = []
        for p in parents:
            p_list.append({'id': p.id, 'name': p.name, 'lastname': p.lastname})
        res = {'parents': p_list}

        # hypermedia
        for i in range(min(10, len(parents))):
            links += build_link('admin_parent_with_id', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/parent')

        return build_response(res, links=links)


@app.route('/admin/parent/<int:parent_id>/')
@auth_check
def admin_parent_with_id(parent_id):
    '''Info and index for this parent'''

    # hypermedia
    links = build_link('admin_parent_with_id', parent_id=parent_id, rel='self')
    links += build_link('admin_parent', rel='http://relations.highschool.com/parentlist')
    links += build_link('admin_parent', rel='http://relations.highschool.com/createparent')
    links += build_link('admin', rel='http://relations.highschool.com/index')

    # query info
    t = session.query(Parent).get(parent_id)

    # check query result
    if not t:
        return build_response(error='Teacher not found.', links=links)

    # build response
    t_obj = {'id': t.id, 'name': t.name, 'lastname': t.lastname}
    res = {'teacher': t_obj}

    # hypermedia
    links += build_link('notification_parent_with_id', parent_id=parent_id,
                        rel='http://relations.highschool.com/notificationlist')
    links += build_link('notification_parent_with_id', parent_id=parent_id,
                        rel='http://relations.highschool.com/createnotification')
    links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/paymentlist')
    links += build_link('payment_parent', parent_id=parent_id, rel='http://relations.highschool.com/createpayment')

    return build_response(res, links=links)


@app.route('/admin/class/')
@auth_check
def classes():
    '''Show list of classes'''

    # hypermedia
    links = build_link('classes', rel='self')
    links += build_link('classes', rel='http://relations.highschool.com/classlist')
    links += build_link('admin', rel='http://relations.highschool.com/index')

    # query classes
    classes = session.query(Class).all()

    # check query result
    if not classes:
        return build_response(error='No classes found.', links=links), 404

    # response
    c_list = []
    for c in classes:
        c_list.append({'id': c.id, 'room': c.room, 'name': c.name})
    res = {'classes': c_list}

    # hypermedia
    for i in range(min(10, len(classes))):
        links += build_link('class_with_id', class_id=classes[i].id,
                            rel='http://relations.highschool.com/class')

    return build_response(res, links=links)


@app.route('/admin/class/<int:class_id>/')
@auth_check
def class_with_id(class_id):
    '''Show class info'''

    # hypermedia
    links = build_link('class_with_id', class_id=class_id, rel='self')
    links += build_link('class_with_id', class_id=class_id, rel='http://relations.highschool.com/class')
    links += build_link('classes', rel='http://relations.highschool.com/classlist')
    links += build_link('admin', rel='http://relations.highschool.com/index')

    # query
    c = session.query(Class).get(class_id)

    # check query result
    if not c:
        return build_response(error='Class not found.', links=links), 404

    # response
    c_obj = {'id': c.id, 'room': c.room, 'name': c.name}
    res = {'class': c_obj}

    # hypermedia
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

    # hypermedia
    links = build_link('classes', rel='http://relations.highschool.com/classlist')
    links += build_link('admin', rel='http://relations.highschool.com/index')
    links += build_link('class_student', class_id=class_id, rel='self')
    links += build_link('class_student', class_id=class_id, rel='http://relations.highschool.com/studentlist')

    # check input
    c = session.query(Class).get(class_id)
    if not c:
        return build_response(error='Class not found.', links=links), 404

    # query
    students = session.query(Student).filter_by(class_id=class_id).all()

    # check query result
    if not students:
        return build_response(error='No students found.', links=links), 404

    # build object
    s_list = []
    for s in students:
        s_list.append(
            {'id': s.id, 'name': s.name, 'lastname': s.lastname, 'parent_id': s.parent_id, 'class_id': s.class_id})
    res = {'students': s_list}

    # hypermedia
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

        response = build_response(res, links=links)
        response.headers['Location'] = url_for('student_with_id', student_id=new_id)
        return response, 201

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
            date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
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
        parents = session.query(Parent).limit(3).all()
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
            date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
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

        response = build_response(res, links=links)
        response.headers['Location'] = url_for('admin_parent_with_id', parent_id=parent_id)
        return response, 201

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
        amount = data['amount']
        date = data['date']
        reason = data['reason']
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

        response = build_response(res, links=links)
        response.headers['Location'] = url_for('class_with_id', class_id=class_id)
        return response, 201

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
        links = build_link('notification', rel='self')
        links += build_link('notification', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification', rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        links += build_link('notification_parents', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_parents', rel='http://relations.highschool.com/createnotification')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/createnotification')
        classes = session.query(Class).limit(3).all()
        for i in range(min(3, len(classes))):
            links += build_link('notification_class', class_id=classes[i].id,
                                rel='http://relations.highschool.com/notificationlist')
            links += build_link('notification_class', class_id=classes[i].id,
                                rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links), 201

    else:
        '''List school-wide notifications'''

        # hypermedia
        links = build_link('notification', rel='self')
        links += build_link('notification', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification', rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        links += build_link('notification_parents', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_parents', rel='http://relations.highschool.com/createnotification')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/createnotification')
        classes = session.query(Class).limit(3).all()
        for i in range(min(3, len(classes))):
            links += build_link('notification_class', class_id=classes[i].id,
                                rel='http://relations.highschool.com/notificationlist')
            links += build_link('notification_class', class_id=classes[i].id,
                                rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links)


@app.route('/admin/notification/parent/', methods=['GET', 'POST'])
def notification_parents():
    if request.method == 'POST':
        '''Create a notification for all parents'''

        # hypermedia
        links = build_link('notification_parents', rel='self')
        links += build_link('notification_parents', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_parents', rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        parents = session.query(Parent).limit(5).all()
        for i in range(min(5, len(parents))):
            links += build_link('notification_parent_with_id', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/notificationlist')
            links += build_link('notification_parent_with_id', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links), 201

    else:
        '''List notifications for all parents'''

        # hypermedia
        links = build_link('notification_parents', rel='self')
        links += build_link('notification_parents', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_parents', rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        parents = session.query(Parent).limit(5).all()
        for i in range(min(5, len(parents))):
            links += build_link('notification_parent_with_id', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/notificationlist')
            links += build_link('notification_parent_with_id', parent_id=parents[i].id,
                                rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links)


@app.route('/admin/notification/parent/<int:parent_id>/', methods=['GET', 'POST'])
@auth_check
def notification_parent_with_id(parent_id):
    if request.method == 'POST':
        '''Create a notification for a single parent'''

        # hypermedia
        links = build_link('notification_parent_with_id', parent_id=parent_id, rel='self')
        links += build_link('notification_parent_with_id', parent_id=parent_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_parent_with_id', parent_id=parent_id,
                            rel='http://relations.highschool.com/createnotification')
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

        return build_response(res, links=links), 201

    else:
        '''List notifications for this parent'''

        # hypermedia
        links = build_link('notification_parent_with_id', parent_id=parent_id, rel='self')
        links += build_link('notification_parent_with_id', parent_id=parent_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_parent_with_id', parent_id=parent_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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

        return build_response(res, links=links)


@app.route('/admin/notification/teacher/', methods=['GET', 'POST'])
@auth_check
def notification_teachers():
    if request.method == 'POST':
        '''Create a notification for all teachers'''

        # hypermedia
        links = build_link('notification_teachers', rel='self')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        teachers = session.query(Teacher).limit(5).all()
        for i in range(min(5, len(teachers))):
            links += build_link('notification_teacher_with_id', teacher_id=teachers[i].id,
                                rel='http://relations.highschool.com/notificationlist')
            links += build_link('notification_teacher_with_id', teacher_id=teachers[i].id,
                                rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links), 201

    else:
        '''List notifications for all teachers'''

        # hypermedia
        links = build_link('notification_teachers', rel='self')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_teachers', rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        teachers = session.query(Teacher).limit(5).all()
        for i in range(min(5, len(teachers))):
            links += build_link('notification_teacher_with_id', teacher_id=teachers[i].id,
                                rel='http://relations.highschool.com/notificationlist')
            links += build_link('notification_teacher_with_id', teacher_id=teachers[i].id,
                                rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links)


@app.route('/admin/notification/teacher/<int:teacher_id>/', methods=['GET', 'POST'])
@auth_check
def notification_teacher_with_id(teacher_id):
    if request.method == 'POST':
        '''Create a notification for a single teacher'''

        # hypermedia
        links = build_link('notification_teacher_with_id', teacher_id=teacher_id, rel='self')
        links += build_link('notification_teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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

        return build_response(res, links=links), 201

    else:
        '''List notifications for a single teacher'''

        # hypermedia
        links = build_link('notification_teacher_with_id', teacher_id=teacher_id, rel='self')
        links += build_link('notification_teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_teacher_with_id', teacher_id=teacher_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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

        return build_response(res, links=links)


@app.route('/admin/notification/class/<int:class_id>/', methods=['GET', 'POST'])
@auth_check
def notification_class(class_id):
    if request.method == 'POST':
        '''Create a class-wide notification'''

        # hypermedia
        links = build_link('notification_class', class_id=class_id, rel='self')
        links += build_link('notification_class', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
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
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links), 201

    else:
        '''List class-wide notifications'''

        # hypermedia
        links = build_link('notification_class', class_id=class_id, rel='self')
        links += build_link('notification_class', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')

        return build_response(res, links=links)


@app.route('/admin/notification/class/<int:class_id>/parents/', methods=['GET', 'POST'])
@auth_check
def notification_class_parents(class_id):
    if request.method == 'POST':
        '''Create a notification for the parents in a class'''

        # hypermedia
        links = build_link('notification_class_parents', class_id=class_id, rel='self')
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
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

        return build_response(res, links=links), 201

    else:
        '''List all notifications for the parents in a class'''

        # hypermedia
        links = build_link('notification_class_parents', class_id=class_id, rel='self')
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_parents', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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

        return build_response(res, links=links)


@app.route('/admin/notification/class/<int:class_id>/teachers/', methods=['GET', 'POST'])
@auth_check
def notification_class_teachers(class_id):
    if request.method == 'POST':
        '''Create a notification for the teachers in a class'''

        # hypermedia
        links = build_link('notification_class_teachers', class_id=class_id, rel='self')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
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

        return build_response(res, links=links), 201

    else:
        '''List all notifications for the teachers in a class'''

        # hypermedia
        links = build_link('notification_class_teachers', class_id=class_id, rel='self')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/notificationlist')
        links += build_link('notification_class_teachers', class_id=class_id,
                            rel='http://relations.highschool.com/createnotification')
        links += build_link('admin', rel='http://relations.highschool.com/index')

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

        return build_response(res, links=links)

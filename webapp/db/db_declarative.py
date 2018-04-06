from sqlalchemy import Table, Column, ForeignKey, CheckConstraint
from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
import IPython
from datetime import datetime, timedelta



def create_session():
    # A session object is created.
    DBSession = sessionmaker(bind=engine)
    # A DBSession() instance establishes all conversations with the database
    # and represents a "staging zone" for all the objects loaded into the
    # database session object. Any change made against the objects in the
    # session won't be persisted into the database until you call
    # session.commit(). If you're not happy about the changes, you can
    # revert all of them back to the last commit by calling
    # session.rollback()
    return DBSession()

# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///webapp/db/highschool.db')


def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')


from sqlalchemy import event

event.listen(engine, 'connect', _fk_pragma_on_connect)


# A declarative base class is created with the declarative_base() function.
Base = declarative_base()

teachers_classes_table = Table('teachers_classes', Base.metadata,
                               Column('teacher_id', Integer, ForeignKey('teacher.id')),
                               Column('class_id', Integer, ForeignKey('class.id'))
                               )

# probabilmente non è il modo migliore di gestire le notification
# teachers_notifications_table = Table('teachers_notifications', Base.metadata,
#                                      Column('teacher_id', Integer, ForeignKey('teacher.id')),
#                                      Column('notification_id', Integer, ForeignKey('notification.id'))
#                                      )

# parents_notifications_table = Table('parents_notifications', Base.metadata,
#                                     Column('parent_id', Integer, ForeignKey('parent.id')),
#                                     Column('notification_id', Integer, ForeignKey('notification.id'))
#                                     )

# classes_notifications_table = Table('classes_notifications', Base.metadata,
#                                     Column('class_id', Integer, ForeignKey('class.id')),
#                                     Column('notification_id', Integer, ForeignKey('notification.id'))
#                                     )

# students_notifications_table = Table('students_notifications', Base.metadata,
#                                      Column('student_id', Integer, ForeignKey('student.id')),
#                                      Column('notification_id', Integer, ForeignKey('notification.id'))
#                                      )


class Student(Base):
    __tablename__ = 'student'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey('parent.id'))
    #    notifications = relationship("Notification", secondary=students_notifications_table, backref='students')
    class_id = Column(Integer, ForeignKey('class.id'))
    grades = relationship("Grade")


class Teacher(Base):
    __tablename__ = 'teacher'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    subjects = relationship("Subject")
    appointments = relationship("Appointment")
    classes = relationship("Class", secondary=teachers_classes_table, backref="teachers", lazy='immediate')


#    notifications = relationship("Notification", secondary=teachers_notifications_table, backref='teachers')



class Subject(Base):
    # todo unire in qualche modo con class teacher table
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    name = Column(String(10), nullable=False)
    timetable = Column(String(500), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teacher.id'))
    class_id = Column(Integer, ForeignKey('class.id'))


class Parent(Base):
    __tablename__ = 'parent'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    children = relationship("Student")
    appointments = relationship("Appointment")
    #    notifications = relationship("Notification", secondary=parents_notifications_table, backref='parents')
    payments = relationship("Payment")


class Class(Base):
    __tablename__ = 'class'
    id = Column(Integer, primary_key=True)
    name = Column(String(2), nullable=False, unique=True)
    room = Column(String(5), nullable=False)
    #    notifications = relationship("Notification", secondary=classes_notifications_table, backref='classes')
    students = relationship("Student")
    subjects = relationship("Subject")


class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    text = Column(String(10000))
    scope = Column(String(20), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teacher.id'))
    parent_id = Column(Integer, ForeignKey('parent.id'))
    class_id = Column(Integer, ForeignKey('class.id'))
    # constraints
    scopes_list = "('all', 'teachers', 'parents', 'one_teacher', 'one_parent', 'class', 'class_teachers', 'class_parents')"
    __table_args__ = (
        # possible scopes
        CheckConstraint("scope IN " + scopes_list),
        # one_teacher => teacher_id is set
        CheckConstraint("NOT (scope == 'one_teacher') OR teacher_id IS NOT NULL"),
        # teacher_id is set => one_teacher
        CheckConstraint("teacher_id IS NULL OR scope == 'one_teacher'"),
        # one_parent => parent_id is set
        CheckConstraint("NOT (scope == 'one_parent') OR parent_id IS NOT NULL"),
        # parent_id is set => one_parent
        CheckConstraint("parent_id IS NULL OR scope == 'one_parent'"),
        # class, class_teachers, class_parents => class_id is set
        CheckConstraint("NOT scope IN ('class', 'class_teachers', 'class_parents') OR class_id IS NOT NULL"),
        # class_id is set => class, class_teachers, class_parents
        CheckConstraint("class_id IS NULL OR scope IN ('class', 'class_teachers', 'class_parents')")
    )



class Appointment(Base):
    __tablename__ = 'appointment'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    room = Column(String(5), nullable=True)
    teacher_accepted = Column(Boolean, nullable=False)
    parent_accepted = Column(Boolean, nullable=False)
    teacher_id = Column(Integer, ForeignKey('teacher.id'))
    parent_id = Column(Integer, ForeignKey('parent.id'))



class Payment(Base):
    __tablename__ = 'payment'
    id = Column(Integer, primary_key=True)
    amount = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(String(200))
    is_pending = Column(Boolean, nullable=False)
    parent_id = Column(Integer, ForeignKey('parent.id'))


# da rivedere, forse meglio un tabellozzo subject+class con tutti i grade?
class Grade(Base):
    __tablename__ = 'grade'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.id'))
    student_id = Column(Integer, ForeignKey('student.id'))
    value = Column(Integer, nullable=False)


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    type = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey('teacher.id'))
    parent_id = Column(Integer, ForeignKey('parent.id'))
    # constraints
    types_list = "('admin', 'teacher', 'parent')"
    __table_args__ = (
        # possible types
        CheckConstraint("type IN " + types_list),
        # teacher => teacher_id is set
        CheckConstraint("NOT (type == 'teacher') OR teacher_id IS NOT NULL"),
        # teacher_id is set => teacher
        CheckConstraint("teacher_id IS NULL OR type == 'teacher'"),
        # parent => parent_id is set
        CheckConstraint("NOT (type == 'parent') OR parent_id IS NOT NULL"),
        # parent_id is set => parent
        CheckConstraint("parent_id IS NULL OR type == 'parent'")
    )

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

# The declarative Base is bound to the database engine.
Base.metadata.create_all(engine)

session = create_session()
# IPython.embed()


# rs = session.query(Parent).first()
# rs.name
# rs.id
# rs.children
# rs.children.name
# rs.children.first()
# list = rs.children
# for l in list:
#     print l.name
# for l in list:
#     print (l.name)
    


# new_parent = Parent(name='Marco', lastname= 'Rossi', pwd='pwd')
# # With the add() method, we add the specified instance of Parent classes
# # to the session.
# session.add(new_parent)

# # The changes are committed to the database with the commit() method.
# session.commit()


# rs = session.query(Parent).all()
# for parent in rs:
#     print(parent.id, parent.name, parent.lastname, parent.pwd)


# new_student = Student(name='Rosa', lastname='Monte', parent_id= 8)
# session.add(new_student)
# session.commit()

# new_appointment = Appointment(date=datetime.strptime('2018-5-3 14:30:00', '%Y-%m-%d %H:%M:%S'), room='A', teacher_accepted=0,parent_accepted=1, teacher_id=2, parent_id=1)
# session.add(new_appointment)
# session.commit()


# new_payment = Payment(date=datetime.strptime('2017-5-3 14:30:00', '%Y-%m-%d %H:%M:%S'), amount=500,reason='enrollment taxes', is_pending=0,parent_id=1)
# session.add(new_payment)
# session.commit()

# new_notification = Notification(date=datetime.strptime('2018-4-6', '%Y-%m-%d'), text='prova per class_parents', scope='class_parents', parent_id=1)
# session.add(new_notification)
# session.commit()

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy import create_engine, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker


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
engine = create_engine('sqlite:///highschool.db')

# A declarative base class is created with the declarative_base() function.
Base = declarative_base()

teachers_classes_table = Table('teachers_clases', Base.metadata,
                               Column('teacher_id', Integer, ForeignKey('teacher.id')),
                               Column('class_id', Integer, ForeignKey('class.id'))
                               )

# probabilmente non è il modo migliore di gestire le notification
teachers_notifications_table = Table('teachers_notifications', Base.metadata,
                                     Column('teacher_id', Integer, ForeignKey('teacher.id')),
                                     Column('notification_id', Integer, ForeignKey('notification.id'))
                                     )

parents_notifications_table = Table('parents_notifications', Base.metadata,
                                    Column('parent_id', Integer, ForeignKey('parent.id')),
                                    Column('notification_id', Integer, ForeignKey('notification.id'))
                                    )

classes_notifications_table = Table('classes_notifications', Base.metadata,
                                    Column('class_id', Integer, ForeignKey('class.id')),
                                    Column('notification_id', Integer, ForeignKey('notification.id'))
                                    )

students_notifications_table = Table('students_notifications', Base.metadata,
                                     Column('student_id', Integer, ForeignKey('student.id')),
                                     Column('notification_id', Integer, ForeignKey('notification.id'))
                                     )


class Student(Base):
    __tablename__ = 'student'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey('parent.id'))
    notifications = relationship("Notification", secondary=students_notifications_table, backref='students')
    class_id = Column(Integer, ForeignKey('class.id'))
    grades = relationship("Grade")


class Teacher(Base):
    __tablename__ = 'teacher'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    pwd = Column(String(16), nullable=False)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    subjects = relationship("Subject")
    appointments = relationship("Appointment")
    classes = relationship("Class", secondary=teachers_classes_table, backref="teachers")
    notifications = relationship("Notification", secondary=teachers_notifications_table, backref='teachers')


class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    # timetable??
    teacher_id = Column(Integer, ForeignKey('teacher.id'))


class Parent(Base):
    __tablename__ = 'parent'
    # Here we define columns for the table address.
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    pwd = Column(String(16), nullable=False)
    name = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    children = relationship("Student")
    appointments = relationship("Appointment")
    notifications = relationship("Notification", secondary=parents_notifications_table, backref='parents')
    payments = relationship("Payment")


class Class(Base):
    __tablename__ = 'class'
    id = Column(Integer, primary_key=True)
    name = Column(String(2), nullable=False, unique=True)
    room = Column(String(5), nullable=False)
    notifications = relationship("Notification", secondary=classes_notifications_table, backref='classes')
    students = relationship("Student")


class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    # scope =


class Appointment(Base):
    __tablename__ = 'appointment'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    room = Column(String(5), nullable=False)
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
    date = Column(DateTime, primary_key=True)
    subject_id = Column(Integer, primary_key=True)  # se ID che non esiste? controlliamo mo o poi?
    student_id = Column(Integer, ForeignKey('student.id'))


# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

# The declarative Base is bound to the database engine.
Base.metadata.create_all(engine)

session = create_session()


# new_parent = Parent(name='Marco', lastname= 'Rossi', pwd='pwd')
# # With the add() method, we add the specified instance of Parent classes
# # to the session.
# session.add(new_parent)

# # The changes are committed to the database with the commit() method.
# session.commit()


rs = session.query(Parent).all()
for parent in rs:
    print(parent.id, parent.name, parent.lastname, parent.pwd)

# IPython.embed()
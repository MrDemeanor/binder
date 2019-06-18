from app import db
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


"""
User Model

@Parameters
    
"""

class UserModel(UserMixin, db.Model):

    __tablename__ = "user_model"

    # Texas State NetID is the primary key
    id = db.Column(db.String(64), primary_key=True)

    # Email of the Student Worker
    email = db.Column(db.String(120), index=True, unique=True)

    # First name of the Student Worker
    firstname = db.Column(db.String(64), index=True, unique=False)

    # Last name of the Student Worker
    lastname = db.Column(db.String(64), index=True, unique=False)

    # What department does the Student Worker work for?
    department = db.Column(db.String(64), index=True, unique=False)

    # What classes does this department control
    class_jurisdiction = db.Column(db.String(256), index=False, unique=False)

    # We do not store passwords directly, only the hash of a password
    password_hash = db.Column(db.String(128))

    # Level of authentication. 0 is regular user, 1 is Admin (like Pam or Denise), and 2 is SysAdmin (create accounts)
    authentication_level = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<User {}>'.format(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


"""
Semester Model

@Parameters
    
"""

class SemesterModel(db.Model):

    __tablename__ = "semester"

    # ID of the semester will contain the department name (or possibly acronym) and the code that MGT used...remember? 
    id = db.Column(db.String(64), primary_key=True)

    # Spring, Summer, or Fall?
    season = db.Column(db.String(64), index=True)

    # Year
    year = db.Column(db.Integer, index=True)
    
    # What department does this semester pertain to?
    department = db.Column(db.String(64), index=True, unique=False)

    # Semesters can have many classes
    classes = db.relationship('ClassModel', backref='semester', lazy='dynamic')

    def __repr__(self):
        return '<Semester {}>'.format(self.id)


"""
Class Model

@Parameters
    
"""

class ClassModel(db.Model):

    __tablename__ = "class"

    # ID will be the class name plus section number; plain and simple. Eg: "MGT 3303 234 Spring 2019", "MGT 4335 254 Fall 2018", etc...so it's "department + class_number + class_section + season + year"
    id = db.Column(db.String(64), primary_key=True)

    # Every class has a number. Eg: MGT 3303. We want the 3303 part, get it?
    class_number = db.Column(db.String(64), index=True, unique=False)

    # Class section number
    class_section = db.Column(db.String(64), index=True, unique=False)
    
    # What department does this class pertain to?
    department = db.Column(db.String(64), index=True, unique=False)

    # What is the name of the subject
    subject = db.Column(db.String(64), index=True, unique=False)

    # Professor teaching the class
    professor = db.Column(db.String(64), index=True, unique=False)

    # Eg: MCCOY, ASBN, FH, etc. As it shows up on Catsweb
    class_location = db.Column(db.String(64), index=True, unique=False)

    # Current enrollment number divided by maximum capacity
    percentage_filled = db.Column(db.Float, index=True, unique=False, default=0)
    
    # Maximum number of students that the class can hold
    max_capacity = db.Column(db.Integer, index=True, unique=False)

    # Number of students that are currently enrolled in the class. Try to scrape off of Catsweb
    num_enrolled_students = db.Column(db.Integer, index=True, unique=False)

    # Number of enrolled students + number of students who have received an override but haven't registered yet
    potentially_enrolled_students = db.Column(db.Integer, index=True, unique=False, default=0)

    # Semester that this class belongs to
    season = db.Column(db.String(10), index=True, unique=False)

    # Year that this class is taking place in
    year = db.Column(db.Integer, index=True, unique=False)

    # Days of the week that the class is taking place
    days = db.Column(db.String(5), index=True, unique=False)

    # Time of class
    class_time = db.Column(db.String(64), index=True, unique=False)
    
    # Classes map back to semesters
    semester_id = db.Column(db.String(64), db.ForeignKey('semester.id'))

    # Classes have many overrides
    overrides = db.relationship('OverrideModel', backref='university_class', lazy='dynamic')

    def __repr__(self):
        return '<Class {} {}>'.format(self.department, self.class_number)


"""
Override Model

@Parameters
    
"""

class OverrideModel(db.Model):

    __tablename__ = "override"

    # ID of override will be '<student_name>-timestamp'
    id = db.Column(db.String(120), index=True, primary_key=True)

    # What student is requesting the override?
    student_name = db.Column(db.String(64), index=True, unique=False)

    # Students A0 number
    student_A_number = db.Column(db.String(64), index=True, unique=False)

    # Has the student registered yet
    registration_status = db.Column(db.Boolean, default=False, nullable=False)

    # Which user created this override?
    creator = db.Column(db.String(10), index=True, unique=False)

    # Student NetID
    student_netid = db.Column(db.String(10), index=True, unique=False)

    # Date created
    date_created = db.Column(db.String(10), index=True, unique=False)

    # Map override back to class
    class_id = db.Column(db.String(64), db.ForeignKey('class.id'))

    # Semester that this class belongs to
    season = db.Column(db.String(10), index=True, unique=False)

    # Year that this class is taking place in
    year = db.Column(db.Integer, index=True, unique=False)

    # Days active
    days_active = db.Column(db.Integer, index=True, unique=False, default=7)

    # What department does the Student Worker work for?
    department = db.Column(db.String(64), index=True, unique=False)

    def __repr__(self):
        return '<Override {}>'.format(self.id)

@login.user_loader
def load_user(id):
    return UserModel.query.get(str(id))
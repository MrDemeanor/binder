from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import app, db
from flask import session, Session, jsonify, abort, render_template, flash, redirect, url_for, request, make_response
from flask_restful import Resource, Api, reqparse
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel
from sqlalchemy.exc import DatabaseError
from app.serializers import user_schema, user_schema_many, semester_schema, semester_schema_many, class_schema, class_schema_many, override_schema, override_schema_many
import pdfkit
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import time
import json
from math import ceil
import datetime
import requests
from bs4 import BeautifulSoup
import base64
import smtplib, ssl
from passgen import passgen

# Creates an API instance for flask restful
api = Api(app)

def get_image_file_as_base64_data():
    """
        Returns image as base 64 encoded data to put in semester report PDF file
    """
    with open('app/static/img/txst-primary.png', 'r') as image_file:
        return base64.b64encode(image_file.read())

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """
        Check the level of authentication of the current user. If the current user has Sys Admin
        privileges, render the sys_admin page. Otherwise, load the regular index page.
    """
    departments = json.load(open("configs/departments.json"))["departments"]
    if current_user.authentication_level < 3:
        for department in departments:
            if current_user.department == department["catsweb_val"]:
                departments = department
                break

        return render_template('index.html', name=current_user.firstname, departments=departments)
    else:
        users = UserModel.query.all()
        return render_template('admin.html', name=current_user.firstname, departments=departments, users=users)

@app.route('/create_semester_report', methods=['GET'])
@login_required
def create_semester_report():
    """
        Makes a PDF document with each class in the current semester and lists every override for each class
    """

    # Get the semester and year from http arguments
    semester = request.args.get('semester')
    year = request.args.get('year')

    # Query for the current semester
    this_semester = SemesterModel.query.filter_by(id=current_user.department + "-" + semester + "-" + str(year)).first()
    rendered = render_template('semester_report.html', classes=this_semester.classes.all(), department=current_user.department, semester=semester, year=year)
    pdf = pdfkit.from_string(rendered, False)

    # Tell the browser what to expect as a response (in this case, a PDF document)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=' + current_user.department + '-' + semester + '-' + year + '.pdf'

    return response


@app.route('/logout')
def logout():
    """
        Logout current user
    """
    logout_user()
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Logs in user with server side form validation
    """
    error = None
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = UserModel.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            error = 'Incorrect password.'
            if user is None:
                error = 'User not found. Please try a different email address.'
            flash('Invalid username or password')
            return render_template('login.html', title='Sign In', form=form, error=error)
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form, error=error)

def send_email(receiver_email, receiver_name, password):
    """
        Sends the user of the newly created account an email with their randomly generated password
    """

    # Open email settings
    smtp_settings = json.load(open("configs/smtp_settings.json"))

    sender_email = smtp_settings["sender_email"]

    message = MIMEMultipart("alternative")
    message["Subject"] = "Welcome to Binder!"
    message["From"] = sender_email
    message["To"] = receiver_email

    # TODO: Make these into rendered templates
    # Create the plain-text and HTML version of your message
    text = """\
    Hi, {},
    Thank you for joining Binder! Below is your temporary password to log in. Once logged in, please change your password by selecting the 'Change Password' option in the top right hand corner.
    Temporary Password: {}
    Best, 
    - The Binder Team
    """.format(receiver_name, password)

    html = """\
    <html>
    <body>
        <p>Hi, {}<br><br>
        Thank you for joining Binder! Below is your temporary password to log in. Once logged in, please change your password by selecting the 'Change Password' option in the top right hand corner. <br><br>
        Temporary Password: <strong>{}</strong><br><br>
        Best, <br>
        - The Binder Team
        </p>
    </body>
    </html>
    """.format(receiver_name, password)

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_settings["smtp_url"], smtp_settings["port"], context=context) as server:
        server.login(sender_email, smtp_settings["password"])
        server.sendmail(sender_email, receiver_email, message.as_string())

class CreateNewUser(Resource):
    """
        Makes a new user in the database and then sends the new user their password. 
    """
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('firstname', type=str)
        parser.add_argument('lastname', type=str)
        parser.add_argument('netID', type=str)
        parser.add_argument('department', type=str)
        parser.add_argument('authorization_level', type=int)

        self.args = parser.parse_args()

    def post(self):
        # Checks for proper authorization
        if current_user.authentication_level is 3:

            # Create class jurisdiction string
            departments = json.load(open("configs/departments.json"))

            class_jurisdiction = ""

            for i in range(len(departments["departments"])):
                if self.args["department"] == departments["departments"][i]["catsweb_val"]:
                    for j in range(len(departments["departments"][i]["jurisdiction"])):
                        if j == len(departments["departments"][i]["jurisdiction"]) - 1:
                            class_jurisdiction = class_jurisdiction + departments["departments"][i]["jurisdiction"][j]
                        else:
                            class_jurisdiction = class_jurisdiction + departments["departments"][i]["jurisdiction"][j] + ","
                    break

            try:
                new_user = UserModel(
                    id=self.args["netID"],
                    firstname=self.args["firstname"],
                    lastname=self.args["lastname"],
                    email=self.args["netID"] + '@txstate.edu',
                    department=self.args["department"],
                    authentication_level=self.args["authorization_level"],
                    class_jurisdiction=class_jurisdiction
                )

                # Creates a random password for the new user's account and then adds user to database
                new_password = passgen(length=12, punctuation=False, digits=True, letters=True, case='both')
                new_user.set_password(new_password)
                db.session.add(new_user)
                db.session.commit()

                # Send the new user an email with their new password
                send_email(self.args["netID"] + '@txstate.edu', self.args["firstname"], new_password)

                return { "status": True, "message": "User " + self.args["netID"] + " successfully created! Please reload the page. " }
            except Exception as e: 
                db.session.delete(new_user)
                db.session.commit()
                return { "status": False, "message": "Error!" }
        else:
            return { "status": False, "message": "You do not have the proper credentials to create a user" }

class User(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('firstname', type=str)
        parser.add_argument('lastname', type=str)
        parser.add_argument('department', type=str)
        parser.add_argument('authentication_level', type=int)
        
        self.args = parser.parse_args()

    # Query all of the users
    def get(self):
        users = UserModel.query.all()
        return jsonify(users=user_schema_many.dump(users).data) 

    # Create a new users
    def post(self):
        
        try:
            new_user = UserModel(**self.args)
            db.session.add(new_user)
            db.session.commit()

        except DatabaseError:
            return abort(500, 'User profile failed to be created!')

        return jsonify(message='User successfully created!')

    def put(self):
        
        user = UserModel.query.filter_by(id=self.args['id']).first()

        if user:
            try:
                user.id = self.args['id'] 
                user.email = self.args['email'] 
                user.firstname = self.args['firstname']
                user.lastname = self.args['lastname'] 
                user.department = self.args['department'] 
                user.authentication_level = self.args['authentication_level']
                db.session.commit()
            except DatabaseError:
                return abort(501, 'User was not updated!')

            return jsonify(message="User was successfully updated!")

        else:
            return abort(500, 'The User did not exist in the database')
        

    def delete(self):
        
        user = UserModel.query.filter_by(id=self.args['netID']).first()

        if user:
            try:
                db.session.delete(user)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The user was not deleted')

            return jsonify(message="The user was successfully deleted from the database")

        else:
            return abort(503, 'The user did not exist')

class GetSpecificClass(Resource): 
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('class_number', type=str)
        parser.add_argument('class_section', type=str)
        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=str)
        parser.add_argument('subject', type=str)
        
        self.args = parser.parse_args()
    
    def get(self): 
        specific_class = ClassModel.query.filter_by(
            id=self.args["subject"] + "-" + self.args["class_number"] + "-" + self.args["class_section"] + "-" + self.args["semester"] + "-" + self.args["year"]
        )

        return jsonify(specific_class = class_schema_many.dump(specific_class).data)

class ChangeUserDepartment(Resource):
    """
        In the case that a user changes departments, we are able to change that setting
    """
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('netID', type=str)
        parser.add_argument('department', type=str)
        
        self.args = parser.parse_args()
    
    def post(self):
        if current_user.authentication_level is 3:
            try:
                user = UserModel.query.filter_by(id=self.args["netID"]).first()
                user.department = self.args["department"]
                db.session.commit()
                return { "status": True, "message": "User department successfully changed!" }
            except:
                return { "status": False, "message": "Error!"}
        
        else:
            return { "status": False, "message": "You do not have the proper credentials to change a user's department." }

class ChangeUserAuthentication(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('netID', type=str)
        parser.add_argument('authorization', type=int)
        
        self.args = parser.parse_args()
    
    def post(self):
        if current_user.authentication_level is 3:
            try:
                user = UserModel.query.filter_by(id=self.args["netID"]).first()
                user.authentication_level = self.args["authorization"]
                db.session.commit()
                return { "status": True, "message": "User authentication successfully changed!" }
            except:
                return { "status": False, "message": "Error!" }
        else:
            return { "status": False, "message": "You do not have the proper credentials to change a user's authentication level." }

        
class GetDepartmentSpecificSemesterYears(Resource):
    def get(self):
        semesters = SemesterModel.query.filter_by(department=current_user.department)
        
        years = []
        seasons = []
        
        for semester in semesters:
            if semester.year not in years:
                years.append(semester.year)

        for semester in semesters:
            if semester.season not in seasons:
                seasons.append(semester.season)

        return jsonify(years_and_seasons = { "years": years, "seasons": seasons })

class GetClassNumbers(Resource):
    def get(self):
        
        semester = SemesterModel.query.filter_by(season=request.args["semester"], year=request.args["year"], department=current_user.department).first()
        classes = ClassModel.query.filter_by(semester_id=semester.id)

        print("Fetching classes for {} Department -- {}, {}".format(current_user.department, semester.season, str(semester.year)))

        all_classes = json.loads(json.dumps(class_schema_many.dump(classes).data, indent=4))

        class_numbers = []

        for university_class in all_classes:
            if university_class["class_number"] not in class_numbers:
                class_numbers.append(university_class["class_number"])

        page = render_template('classes_frame_template.html', class_numbers = class_numbers, all_classes = all_classes)
        
        return { "page": page, "class_numbers": class_numbers }

class GetClassSections(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=str)
        parser.add_argument('class_number', type=str)
        
        self.args = parser.parse_args()

    def get(self):
        semester_id = current_user.department + "-" + self.args["semester"] + "-" + str(self.args["year"])
        semester = SemesterModel.query.filter_by(id = semester_id).first()

        all_classes = ClassModel.query.filter_by(semester=semester, class_number=self.args["class_number"])

        sections = []

        for single_class in all_classes:
            sections.append(single_class.class_section)
        
        return sections

class FetchClasses(Resource):
    def get(self):
        try:
            semester = SemesterModel.query.filter_by(season=request.args["semester"], year=request.args["year"], department = current_user.department).first()
            classes = ClassModel.query.filter_by(semester_id=semester.id, class_number=request.args["class_number"])

            all_classes = json.loads(json.dumps(class_schema_many.dump(classes).data, indent=4))

            num_rows = ceil(len(all_classes) / 4)
            remainder = len(all_classes) % 4

            if num_rows is 0:
                return {}

            if remainder is 0:
                remainder = 4
            
            all_classes.sort(key = lambda x: x["class_section"], reverse = False)

            for my_class in all_classes:
                print("\n", my_class, "\n")
            
            subject = all_classes[0]["subject"]

            page = render_template('class_template.html', num_rows=num_rows, all_classes=all_classes, remainder=remainder, class_number=request.args["class_number"], subject=subject)

            return { "page": page, "class_number": request.args["class_number"] }
        except:
            logout_user(current_user)

class DisplaySpecificClass(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=int)
        parser.add_argument('class_number', type=str)
        
        self.args = parser.parse_args()
    
    def get(self):
        classes = ClassModel.query.filter_by(department = current_user.department, class_number = self.args["class_number"], year = self.args["year"], season = self.args["semester"])
        return jsonify(classes = class_schema_many.dump(classes).data)

class Semester(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('season', type=str)
        parser.add_argument('year', type=int)
        
        self.args = parser.parse_args()

    # Query all of the semester
    def get(self):
        semesters = SemesterModel.query.all()
        return jsonify(semesters=semester_schema_many.dump(semesters).data) 

    # Create a new semester
    def post(self):
        try:
            new_semester = SemesterModel(
                id = current_user.department + '-' + self.args["season"] + "-" + str(self.args["year"]), 
                department = current_user.department, 
                season = self.args["season"], 
                year = self.args["year"]
            )
            db.session.add(new_semester)
            db.session.commit()

        except DatabaseError:
            return abort(500, 'Semester failed to be created!')

        return jsonify(message='Semester successfully created!')

    
    def delete(self):
        semester = SemesterModel.query.filter_by(id=self.args["department"] + '-' + self.args["semester_code"]).first()

        if semester:
            try:
                db.session.delete(semester)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The Semester was not deleted')

            return jsonify(message="The Semester was successfully deleted from the database")

        else:
            return abort(503, 'The Student Worker did not exist')


class Class(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('class_number', type=str)
        parser.add_argument('class_section', type=str)
        parser.add_argument('max_capacity', type=int)
        parser.add_argument('year', type=int)
        parser.add_argument('semester', type=str)
        parser.add_argument('subject', type=str)

        self.args = parser.parse_args()

    # Query all of the classes
    def get(self):
        classes = ClassModel.query.all()
        return jsonify(classes=class_schema_many.dump(classes).data) 

    # Create a new class
    def post(self):
        try:
            if current_user.authentication_level != 2:
                return { "status": False, "message": "Cannot create class: Improper credentials." }
            # Make the semester ID
            semester_id = current_user.department + "-" + self.args["semester"] + "-" + str(self.args["year"])

            # Query for the semester based on the semester ID
            semester = SemesterModel.query.filter_by(id = semester_id).first()

            # Create the new class
            new_class = ClassModel(
                id = current_user.department + "-" + str(self.args["class_number"])  + "-" + str(self.args["class_section"]) + "-" + str(self.args["semester"] + "-" + str(self.args["year"])), 
                class_number = self.args["class_number"], 
                class_section = self.args["class_section"], 
                department = current_user.department,
                max_capacity = self.args["max_capacity"], 
                year = self.args["year"], 
                season = self.args["semester"],
                semester=semester, 
                subject = self.args["subject"]
            )
            db.session.add(new_class)
            db.session.commit()

        except DatabaseError:
            return { "status": False, "message": "Error!" }

        return { "status": True, "message": "Class created!"}

    def put(self):

        university_class = ClassModel.query.filter_by(id = current_user.department + "-" + str(self.args["class_number"])  + "-" + str(self.args["class_section"]) + "-" + str(self.args["semester"] + "-" + str(self.args["year"]))).first()

        if university_class:
            try:
                university_class.id = current_user.department + "-" + str(self.args["class_number"])  + "-" + str(self.args["class_section"]) + "-" + str(self.args["semester"] + "-" + str(self.args["year"])), 
                university_class.class_number = self.args["class_number"], 
                university_class.class_section = self.args["class_section"], 
                university_class.professor = self.args["professor"], 
                university_class.classroom_building = self.args["classroom_building"], 
                university_class.classroom_number = self.args["classroom_number"], 
                university_class.max_capacity = self.args["max_capacity"], 
                university_class.num_enrolled_students = self.args["num_enrolled_students"], 
                university_class.potentially_enrolled_students = self.args["potentially_enrolled_students"]
            except DatabaseError:
                return abort(501, 'Class was not updated!')

            return jsonify(message="Class was successfully updated!")

        else:
            return abort(500, 'The Class did not exist in the database')

    def delete(self):
        university_class = ClassModel.query.filter_by(id=self.args["department"] + "-" + self.args["class_number"] + "-" + self.args["class_section"] + "-" + self.args["semester_code"]).first()

        if university_class:
            try:
                db.session.delete(university_class)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The Class was not deleted')

            return jsonify(message="The Class was successfully deleted from the database")

        else:
            return abort(503, 'The Class did not exist')

class GetOverridesForSpecificClass(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('class_number', type=str)
        parser.add_argument('class_section', type=str)
        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=str)
        parser.add_argument('subject', type=str)

        self.args = parser.parse_args()
    
    def get(self):
        id = self.args["subject"] + "-" + self.args["class_number"] + "-" + self.args["class_section"] + "-" + self.args["semester"] + "-" + self.args["year"]
        print("\n\n", id, "\n\n")
        specific_class = ClassModel.query.filter_by(
            id=id
        ).first()

        overrides = OverrideModel.query.filter_by(class_id=specific_class.id)

        return jsonify(overrides=override_schema_many.dump(overrides).data)

class AlterMaxCapacity(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('class_id', type=str)
        parser.add_argument('max_capacity', type=int)
        
        self.args = parser.parse_args()
    
    def get(self):
        if current_user.authentication_level != 2:
            return { "status": False, "message": "Cannot alter max capacity: Improper credentials. " }
        university_class = ClassModel.query.filter_by(id = self.args["class_id"]).first()
        university_class.max_capacity = self.args["max_capacity"]
        university_class.percentage_filled = university_class.potentially_enrolled_students / university_class.max_capacity
        db.session.commit()
        return { "status": True, "message": "Max capacity changed to " + str(self.args["max_capacity"]) }

class DeleteOverride(Resource):
    def __init__(self): 
        parser = reqparse.RequestParser()

        parser.add_argument('override_id', type=str)
        
        self.args = parser.parse_args()
    
    def get(self):
        try:
            override = OverrideModel.query.filter_by(id = self.args["override_id"]).first()

            override.university_class.potentially_enrolled_students = override.university_class.potentially_enrolled_students - 1
            override.university_class.percentage_filled = override.university_class.potentially_enrolled_students / override.university_class.max_capacity
            db.session.commit()
            db.session.delete(override)
            db.session.commit()
            return jsonify(status=True)
        except:
            return jsonify(status=False)

class GenerateSemesterFromCatsweb(Resource):
    def __init__(self): 
        parser = reqparse.RequestParser()

        parser.add_argument('sid', type=str)
        parser.add_argument('PIN', type=str)
        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=str)
        
        self.args = parser.parse_args()

        print("\n\n")
        print(self.args["sid"])
        print(self.args["PIN"])
        print(self.args["semester"])
        print(self.args["year"])
        print("\n\n")
    
    def post(self):

        if current_user.authentication_level != 2:
            return {"status": False, "message": "Improper credentials"}
        
        user = UserModel.query.filter_by(id=current_user.id).first()

        if current_user.department != user.department:
            logout_user(current_user)

        id = current_user.department + '-' + self.args["semester"] + "-" + str(self.args["year"])
        new_semester = SemesterModel.query.filter_by(id = id).first()
        

        # Determine the term code
        if self.args["semester"] == 'Spring':
            term = self.args["year"] + '30'
        elif self.args["semester"] == 'Summer':
            term = self.args["year"] + '50'
        else:
            term = str(int(self.args["year"]) + 1) + '10'
        
        with requests.Session() as c:

            # Get cookie from the login page
            url = 'https://ssb.txstate.edu/prod/twbkwbis.P_WWWLogin'
            c.get(url)

            # Supply username and password from credentials file
            payload = {
                "sid": self.args["sid"],
                "PIN": self.args["PIN"]
            }

            # Give headers to make it seem like we're not a robot
            headers = {
                "Host": "ssb.txstate.edu",
                "Connection": "keep-alive",
                "Content-Length": "27",
                "Cache-Control": "max-age=0",
                "Origin": "https://ssb.txstate.edu",
                "Upgrade-Insecure-Requests": "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                "Referer": "https://ssb.txstate.edu/prod/twbkwbis.P_WWWLogin",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
            }

            # Make a POST request to the validation login page with the headers and payload
            validate_url = 'https://ssb.txstate.edu/prod/twbkwbis.P_ValLogin'
            response = c.post(validate_url, headers=headers, data=payload)
            
            # Parse response into BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            if soup.title is not None:
                return { "status": False, "message": "Incorrect username or password" }

            if new_semester is None:
                new_semester = SemesterModel(
                    id = current_user.department + '-' + self.args["semester"] + "-" + str(self.args["year"]), 
                    department = current_user.department, 
                    season = self.args["semester"], 
                    year = self.args["year"]
                )
                db.session.add(new_semester)
                db.session.commit()
            else:
                return {"status": 402}

            # Make a request to this link to get a list of all the classes offered at Texas State
            class_jurisdiction_query_string = ""
            for subject in current_user.class_jurisdiction.split(","):
                class_jurisdiction_query_string = class_jurisdiction_query_string + "&sel_subj={}".format(subject)
            print("Jurisdiction! \n\n + {}".format(class_jurisdiction_query_string))
            classes_url = "https://ssb.txstate.edu/prod/bwskfcls.P_GetCrse_Advanced?rsts=dummy&crn=dummy&term_in={}&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy{}&sel_crse=&sel_title=&sel_schd=%25&sel_insm=%25&sel_from_cred=&sel_to_cred=&sel_camp=%25&sel_levl=%25&sel_ptrm=%25&sel_instr=%25&sel_sess=%25&sel_attr=%25&begin_hh=0&begin_mi=0&begin_ap=a&end_hh=0&end_mi=0&end_ap=a&SUB_BTN=Section+Search&path=1".format(term, class_jurisdiction_query_string)
            response = c.get(classes_url)

            # Parse response into BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            all_classes = []
            individual_class = {}

            index = 1

            for td in soup.findAll('td', {'class': 'dddefault'}):
                if index is 1:
                    individual_class["closed_status"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 2:
                    individual_class["CRN"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 3:
                    individual_class["department"] = td.text.strip().replace(" ", "+")
                    index = index + 1
                    continue
                if index is 4:
                    individual_class["class_number"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 5:
                    individual_class["class_section"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 6:
                    individual_class["campus"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 7:
                    individual_class["credit_hours"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 8:
                    individual_class["class_name"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 9:
                    individual_class["days"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 10:
                    individual_class["time"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 11:
                    individual_class["cap"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 12:
                    individual_class["act"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 13:
                    individual_class["rem"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 14:
                    individual_class["wl_cap"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 15:
                    individual_class["wl_act"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 16:
                    individual_class["wl_rem"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 17:
                    individual_class["instructor"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 18:
                    individual_class["date"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 19:
                    individual_class["location"] = td.text.strip()
                    index = index + 1
                    continue
                if index is 20:
                    individual_class["attribute"] = td.text.strip()
                    index = 1
                    all_classes.append(individual_class)
                    individual_class = {}
                    continue

        # Make the classes and add them to the semester
        for scraped_class in all_classes:
            if scraped_class["department"] in current_user.class_jurisdiction.split(","):
                # Make the class!
                try:

                    # Create the new class
                    new_class = ClassModel(
                        id = scraped_class["department"].replace(" ", "+") + "-" + scraped_class["class_number"]  + "-" + scraped_class["class_section"] + "-" + str(self.args["semester"] + "-" + str(self.args["year"])), 
                        class_number = scraped_class["class_number"], 
                        class_section = scraped_class["class_section"], 
                        department = current_user.department,
                        professor = scraped_class["instructor"].replace('(P)', ''), 
                        num_enrolled_students = scraped_class["act"], 
                        potentially_enrolled_students = scraped_class["act"], 
                        class_location = scraped_class["location"],
                        days = scraped_class["days"],
                        class_time = scraped_class["time"], 
                        max_capacity = 300, 
                        percentage_filled = int(scraped_class["act"]) / 300,
                        year = self.args["year"], 
                        season = self.args["semester"],
                        semester=new_semester, 
                        subject = scraped_class["department"].replace(" ", "+")
                    )
                    db.session.add(new_class)

                except DatabaseError:
                    continue

        db.session.commit()
        print("\n\n" + self.args["semester"] + " " + self.args["year"] + " semester created! Please reload the page. " + "\n\n")
        return { "status": True, "message": self.args["semester"] + " " + self.args["year"] + " semester created! Please reload the page. "}

class ChangePassword(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('old_password', type=str)
        parser.add_argument('new_password', type=str)
        parser.add_argument('confirm_password', type=str)
        
        self.args = parser.parse_args()
    
    def post(self):
        if self.args["new_password"] != self.args["confirm_password"]:
            return { "status": False, "message": "Passwords must be the same"}

        if current_user.check_password(self.args["old_password"]):
            current_user.set_password(self.args["new_password"])
            db.session.commit()
            return { "status": True, "message": "Password successfully changed"}
        else:
            return { "status": False, "message": "Old password incorrect"}

class Override(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('student_name', type=str)
        parser.add_argument('student_netid', type=str)
        parser.add_argument('student_A_number', type=str)
        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=str)
        parser.add_argument('class_number', type=str)
        parser.add_argument('class_section', type=str)
        parser.add_argument('days_active', type=int)
        
        self.args = parser.parse_args()

    # Query all of the overrides
    def get(self):
        overrides = OverrideModel.query.all()
        return jsonify(overrides=override_schema_many.dump(overrides).data) 

    # Create a new overrides
    def post(self):
        try:
            university_class = ClassModel.query.filter_by(year = self.args["year"], class_number = self.args["class_number"], class_section = self.args["class_section"], season = self.args["semester"], department = current_user.department).first()
            if university_class.percentage_filled >= 1:
                return { "status": False, "message": str(self.args["class_number"]) + "." + str(self.args["class_section"]) + " filled"}
            university_class.potentially_enrolled_students = university_class.potentially_enrolled_students + 1
            university_class.percentage_filled = university_class.potentially_enrolled_students / university_class.max_capacity
            today = datetime.date.today()
            new_override = OverrideModel(
                id = current_user.department + "-" + self.args["student_name"] + "-" + str(time.time()), 
                student_name = self.args["student_name"], 
                date_created = str(today.month) + "/" + str(today.day) + "/" + str(today.year),
                student_netid = self.args["student_netid"],
                student_A_number = self.args["student_A_number"], 
                creator = current_user.id,  
                season = self.args["semester"], 
                year = self.args["year"],
                department = current_user.department,
                days_active = self.args["days_active"], 
                university_class=university_class
            )
            db.session.add(new_override)
            db.session.commit()

        except DatabaseError:
            return { "status": False, "message": "Error. "}

        return { "status": True, "message": "Override for " + self.args["student_name"] + " added to " + str(self.args["class_number"]) + "." + str(self.args["class_section"])}

    def put(self):

        override = OverrideModel.query.filter_by(student_name = self.args["student_name"], class_number = self.args["class_number"], class_section = self.args["class_section"]).first()

        if override:
            try:
                override.id = self.args["department"] + "-" + self.args["student_name"] + "-" + str(time.time()), 
                override.student_name = self.args["student_name"], 
                override.email = self.args["email"], 
                override.student_A_number = self.args["student_A_number"], 
                override.student_phone_number = self.args["student_phone_number"], 
                override.creator = self.args["creator"],  
            except DatabaseError:
                return abort(501, 'Override was not updated!')

            return jsonify(message="Override was successfully updated!")

        else:
            return abort(500, 'The Override did not exist in the database')

    def delete(self):
        override = OverrideModel.query.filter_by(student_name = self.args["student_name"], class_number = self.args["class_number"], class_section = self.args["class_section"]).first()

        if override:
            try:
                db.session.delete(override)
                db.session.commit()
            except DatabaseError:
                return abort(502, 'The Override was not deleted')

            return jsonify(message="The Override was successfully deleted from the database")

        else:
            return abort(503, 'The Override did not exist')

class GenerateOverrideReport(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('semester', type=str)
        parser.add_argument('year', type=int)

        self.args = parser.parse_args()
    def get(self):
        overrides = OverrideModel.query.filter_by(season=self.args["semester"], year=self.args["year"], department=current_user.department)
        overrides_filtered = []

        for override in overrides:
            
            if override.registration_status == True:
                continue

            # Create datetime object for override date
            override_created_date = override.date_created
            format_str = '%m/%d/%Y'
            override_date = datetime.datetime.strptime(override_created_date, format_str)

            today = datetime.date.today()
            today = str(today.month) + "/" + str(today.day) + "/" + str(today.year)
            today = datetime.datetime.strptime(today, format_str)

            difference = today - override_date

            print("\n\n Difference: {} \n\n".format(difference))

            if difference.days >= override.days_active:
                overrides_filtered.append(override)
        
        return jsonify(overrides=override_schema_many.dump(overrides_filtered).data)


class ChangeRegistrationStatus(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()

        parser.add_argument('override_id', type=str)
        
        self.args = parser.parse_args()
    
    def post(self):
        try:
            override = OverrideModel.query.filter_by(id = self.args["override_id"]).first()
            override.registration_status = not override.registration_status

            if override.registration_status:
                override.university_class.potentially_enrolled_students = override.university_class.potentially_enrolled_students - 1
            else:
                override.university_class.potentially_enrolled_students = override.university_class.potentially_enrolled_students + 1

            db.session.commit()
            return jsonify(status=override.registration_status, potentially_enrolled = override.university_class.potentially_enrolled_students)
        except:
            return abort(502, 'Override was not updated')


# Restful API routes
api.add_resource(User, '/user')
api.add_resource(Semester, '/semester')
api.add_resource(GetDepartmentSpecificSemesterYears, '/get_department_specific_semester_years')
api.add_resource(Class, '/class')
api.add_resource(Override, '/override')
api.add_resource(GetClassNumbers, '/get_class_numbers')
api.add_resource(FetchClasses, '/fetch_classes')
api.add_resource(GetSpecificClass, '/get_specific_class')
api.add_resource(GetOverridesForSpecificClass, '/get_overrides_for_specific_class')
api.add_resource(GetClassSections, '/get_class_sections')
api.add_resource(ChangeRegistrationStatus, '/change_registration_status')
api.add_resource(GenerateOverrideReport, '/generate_override_report')
api.add_resource(DisplaySpecificClass, '/display_specific_class')
api.add_resource(GenerateSemesterFromCatsweb, '/generate_semester_from_catsweb')
api.add_resource(AlterMaxCapacity, '/alter_max_capacity')
api.add_resource(DeleteOverride, '/delete_override')
api.add_resource(CreateNewUser, '/create_new_user')
api.add_resource(ChangeUserDepartment, '/change_user_department')
api.add_resource(ChangeUserAuthentication, '/change_user_authentication')
api.add_resource(ChangePassword, '/change_password')

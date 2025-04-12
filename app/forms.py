from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length

DEPARTMENTS = [("FIST", "FIST"), ("FCI", "FCI"), ("FOB", "FOB")]

class StudentRegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    department = SelectField("Department", choices=DEPARTMENTS, validators=[DataRequired()])
    submit = SubmitField("Register")

class StudentLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class AdminLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class CourseAddForm(FlaskForm):
    course_code = StringField("Course Code", validators=[DataRequired()])
    course_name = StringField("Course Name", validators=[DataRequired()])
    instructor = StringField("Instructor", validators=[DataRequired()])
    quota = IntegerField("Quota", validators=[DataRequired()])
    credits = IntegerField("Credits", validators=[DataRequired()])
    semester = StringField("Semester", validators=[DataRequired()])
    schedule = StringField("Schedule", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    department = SelectField("Department", choices=DEPARTMENTS, validators=[DataRequired()])
    day_of_week = SelectField("Day of Week", choices=[
        ("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"), ("Friday", "Friday")
    ], validators=[DataRequired()])
    start_time = TimeField("Start Time", validators=[DataRequired()])
    end_time = TimeField("End Time", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Add Course")

class CourseEditForm(CourseAddForm):
    submit = SubmitField("Update Course")

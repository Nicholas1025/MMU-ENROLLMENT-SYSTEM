from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class StudentRegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Register")

class StudentLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class AdminLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class CourseEditForm(FlaskForm):
    course_code = StringField("Course Code", validators=[DataRequired()])
    course_name = StringField("Course Name", validators=[DataRequired()])
    instructor = StringField("Instructor", validators=[DataRequired()])
    quota = IntegerField("Quota", validators=[DataRequired()])
    credits = IntegerField("Credits", validators=[DataRequired()])
    semester = StringField("Semester", validators=[DataRequired()])
    schedule = StringField("Schedule", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Update Course")

class CourseAddForm(FlaskForm):
    course_code = StringField("Course Code", validators=[DataRequired()])
    course_name = StringField("Course Name", validators=[DataRequired()])
    instructor = StringField("Instructor", validators=[DataRequired()])
    quota = IntegerField("Quota", validators=[DataRequired()])
    credits = IntegerField("Credits", validators=[DataRequired()])
    semester = StringField("Semester", validators=[DataRequired()])
    schedule = StringField("Schedule", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Add Course")

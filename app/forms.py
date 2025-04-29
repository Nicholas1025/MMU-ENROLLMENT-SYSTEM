from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from wtforms import SelectField

DEPARTMENTS = [("FIST", "FIST"), ("FCI", "FCI"), ("FOB", "FOB")]    

class StudentRegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[
        DataRequired(), 
        Email(), 
    ])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    department = SelectField("Department", choices=DEPARTMENTS, validators=[DataRequired()])
    submit = SubmitField("Register")
    def validate_email(self, field):
        if not field.data.endswith("@student.mmu.edu.my"):
            raise ValidationError("Email must end with @student.mmu.edu.my")

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
    prerequisite_id = SelectField("Prerequisite Course", coerce=int, choices=[], validators=[Optional()])
    course_name = StringField("Course Name", validators=[DataRequired()])
    credits = IntegerField("Credits", validators=[DataRequired()])
    semester = StringField("Semester", validators=[DataRequired()])
    department = SelectField("Department", choices=[
        ("FIST", "FIST"), ("FCI", "FCI"), ("FOB", "FOB")
    ], validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Add Course")
    


class CourseEditForm(CourseAddForm):
    prerequisite_id = SelectField("Prerequisite Course", coerce=int, choices=[], validators=[Optional()])

    submit = SubmitField("Update Course")


class SectionForm(FlaskForm):
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    name = StringField("Section Name", validators=[DataRequired()])
    type = SelectField("Section Type", choices=[("Lecture", "Lecture"), ("Tutorial", "Tutorial"), ("Lab", "Lab")])
    instructor = StringField("Instructor", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    day_of_week = SelectField("Day of Week", choices=[
        ("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"), ("Friday", "Friday")
    ])
    start_time = TimeField("Start Time", validators=[DataRequired()])
    end_time = TimeField("End Time", validators=[DataRequired()])
    quota = IntegerField("Quota", validators=[DataRequired()])
    submit = SubmitField("Save Section")

class SemesterSettingForm(FlaskForm):
    semester = SelectField("Open Semester", choices=[], validators=[DataRequired()])
    submit = SubmitField("Save Semester")


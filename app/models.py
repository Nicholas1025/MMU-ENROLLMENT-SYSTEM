from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)
    department = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))

    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return False

    @property
    def is_student(self):
        return True


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return True

    @property
    def is_student(self):
        return False


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), unique=True)
    course_name = db.Column(db.String(128))
    description = db.Column(db.Text)
    credits = db.Column(db.Integer)
    semester = db.Column(db.String(64))
    department = db.Column(db.String(64))

    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    sections = db.relationship('Section', back_populates='course', cascade='all, delete')


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

    section = db.relationship("Section", back_populates="enrollments")  # ✅ 必加




class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    instructor = db.Column(db.String(64), nullable=False)  # ✅ 加这个
    location = db.Column(db.String(128), nullable=False)    # ✅ 加这个
    day = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)         # ✅ 建议用标准时间类型
    end_time = db.Column(db.Time, nullable=False)
    quota = db.Column(db.Integer, nullable=False)

    course = db.relationship("Course", back_populates="sections")
    enrollments = db.relationship("Enrollment", back_populates="section", cascade="all, delete")



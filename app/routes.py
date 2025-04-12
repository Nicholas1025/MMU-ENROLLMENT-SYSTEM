from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import StudentRegisterForm, StudentLoginForm
from .models import db, Student
from .models import Course, Enrollment
from .forms import CourseAddForm
from .forms import CourseAddForm, AdminLoginForm
from .forms import CourseEditForm

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    form = StudentRegisterForm()
    if form.validate_on_submit():
        existing = Student.query.filter_by(email=form.email.data).first()
        if existing:
            flash("Email already registered.", "warning")
            return redirect(url_for("main.register"))
        
        student = Student(name=form.name.data, email=form.email.data)
        student.set_password(form.password.data)
        db.session.add(student)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)

@main.route("/login", methods=["GET", "POST"])
def login():
    form = StudentLoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data).first()
        if student and student.check_password(form.password.data):
            session["student_id"] = student.id
            flash("Login successful!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html", form=form)

@main.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("main.login"))
    
    courses = Course.query.all()
    student_id = session["student_id"]
    enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=student_id).all()]

    return render_template("dashboard.html", courses=courses, enrolled_ids=enrolled_ids)

@main.route("/enroll/<int:course_id>")
def enroll(course_id):
    if "student_id" not in session:
        return redirect(url_for("main.login"))

    student_id = session["student_id"]
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if existing:
        flash("You already enrolled in this course.", "warning")
    else:
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash("Course registered successfully!", "success")
    
    return redirect(url_for("main.dashboard"))

@main.route("/drop/<int:course_id>")
def drop(course_id):
    if "student_id" not in session:
        return redirect(url_for("main.login"))

    student_id = session["student_id"]
    enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()
        flash("Course dropped.", "info")
    else:
        flash("You are not enrolled in this course.", "danger")

    return redirect(url_for("main.dashboard"))

@main.route("/my-courses")
def my_courses():
    if "student_id" not in session:
        return redirect(url_for("main.login"))
    
    student_id = session["student_id"]
    enrolled = Enrollment.query.filter_by(student_id=student_id).all()
    return render_template("my_courses.html", enrollments=enrolled)

from .models import Course

@main.route("/logout")
def logout():
    session.pop("student_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


from .models import Admin

@main.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            session["admin_id"] = admin.id
            flash("Admin login successful!", "success")
            return redirect(url_for("main.admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("admin_login.html", form=form)

@main.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin_id" not in session:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    form = CourseAddForm()
    courses = Course.query.all()

    if form.validate_on_submit():
        course = Course(
            course_code=form.course_code.data,
            course_name=form.course_name.data,
            instructor=form.instructor.data,
            quota=int(form.quota.data)
        )
        db.session.add(course)
        db.session.commit()
        flash("Course added!", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("admin_dashboard.html", form=form, courses=courses)

@main.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Logged out as admin.", "info")
    return redirect(url_for("main.admin_login"))

@main.route("/admin/delete/<int:course_id>")
def admin_delete(course_id):
    if "admin_id" not in session:
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/admin/edit/<int:course_id>", methods=["GET", "POST"])
def admin_edit(course_id):
    if "admin_id" not in session:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    form = CourseEditForm(obj=course)  # 预填旧数据

    if form.validate_on_submit():
        course.course_code = form.course_code.data
        course.course_name = form.course_name.data
        course.instructor = form.instructor.data
        course.quota = form.quota.data
        course.credits = form.credits.data
        course.semester = form.semester.data
        course.schedule = form.schedule.data
        course.location = form.location.data
        course.description = form.description.data
        db.session.commit()
        flash("Course updated successfully.", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("edit_course.html", form=form, course=course)
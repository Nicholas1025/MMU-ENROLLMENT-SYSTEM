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
        
        student = Student(
            name=form.name.data,
            email=form.email.data,
            department=form.department.data  # ✅ 关键字段！
        )
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
    
    student = Student.query.get(session["student_id"]) 
    courses = Course.query.filter_by(department=student.department).all()
    enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=student.id).all()]

    return render_template("dashboard.html", courses=courses, enrolled_ids=enrolled_ids)

@main.route("/enroll/<int:course_id>")
def enroll(course_id):
    if "student_id" not in session:
        return redirect(url_for("main.login"))

    student_id = session["student_id"]
    course_to_add = Course.query.get_or_404(course_id)

    # ✅ 已选课程检测
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if existing:
        flash("You already enrolled in this course.", "warning")
        return redirect(url_for("main.dashboard"))

    # ✅ Quota 检查
    current_enrolled = Enrollment.query.filter_by(course_id=course_id).count()
    if current_enrolled >= course_to_add.quota:
        flash("Course quota is full.", "danger")
        return redirect(url_for("main.dashboard"))

    # ✅ 时间冲突检查
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.student_id == student_id).all()
    for c in enrolled_courses:
        if c.day_of_week == course_to_add.day_of_week:
            # 先检查双方是否都填了时间
            if all([course_to_add.start_time, course_to_add.end_time, c.start_time, c.end_time]):
                if course_to_add.day_of_week == c.day_of_week:
                    if not (course_to_add.end_time <= c.start_time or course_to_add.start_time >= c.end_time):
                        flash(f"Time conflict with course: {c.course_code}", "danger")
                        return redirect(url_for("main.dashboard"))


    # ✅ 注册课程
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
            quota=int(form.quota.data),
            credits=form.credits.data,
            semester=form.semester.data,
            location=form.location.data,
            description=form.description.data,
            department=form.department.data,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data
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
        print("💡 DEBUG - form data:")
        print("Dept:", form.department.data)
        print("Day:", form.day_of_week.data)
        print("Start:", form.start_time.data)
        print("End:", form.end_time.data)

        course = Course(
            course_code=form.course_code.data,
            course_name=form.course_name.data,
            instructor=form.instructor.data,
            quota=form.quota.data,
            credits=form.credits.data,
            semester=form.semester.data,
            schedule=form.schedule.data,
            location=form.location.data,
            description=form.description.data,
            department=form.department.data,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data
        )
        db.session.add(course)
        db.session.commit()
        flash("Course added!", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("edit_course.html", form=form, course=course)

@main.route("/timetable")
def timetable():
    if "student_id" not in session:
        return redirect(url_for("main.login"))

    student_id = session["student_id"]
    enrolled = Enrollment.query.filter_by(student_id=student_id).all()
    courses = [e.course for e in enrolled]

    return render_template("timetable.html", courses=courses)

@main.route("/admin/course/<int:course_id>/students")
def admin_view_students(course_id):
    if "admin_id" not in session:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    students = [e.student for e in enrollments]

    return render_template("admin_course_students.html", course=course, students=students)


@main.route("/init-demo")
def init_demo():
    from datetime import time
    from .models import Student, Course, Enrollment, db

    # === Create 5 Students (FIST) ===
    students_data = [
        {"name": "Alice Lim", "email": "alice@fist.edu", "department": "FIST"},
        {"name": "Ben Tan", "email": "ben@fist.edu", "department": "FIST"},
        {"name": "Carmen Lee", "email": "carmen@fist.edu", "department": "FIST"},
        {"name": "Daniel Wong", "email": "daniel@fist.edu", "department": "FIST"},
        {"name": "Elena Ng", "email": "elena@fist.edu", "department": "FIST"},
    ]

    for s in students_data:
        if not Student.query.filter_by(email=s["email"]).first():
            student = Student(name=s["name"], email=s["email"], department=s["department"])
            student.set_password("123123")
            db.session.add(student)

    # === Create Courses (All FIST) ===
    courses_data = [
        {
            "course_code": "FIST101",
            "course_name": "Intro to AI",
            "instructor": "Dr. Ling",
            "quota": 30,
            "credits": 3,
            "semester": "Trimester 1",
            "location": "Lab A101",
            "description": "Foundations of Artificial Intelligence.",
            "department": "FIST",
            "day_of_week": "Monday",
            "start_time": time(9, 0),
            "end_time": time(11, 0),
        },
        {
            "course_code": "FIST102",
            "course_name": "Data Science",
            "instructor": "Dr. Tan",
            "quota": 30,
            "credits": 3,
            "semester": "Trimester 1",
            "location": "Lab A102",
            "description": "Data analysis and visualization.",
            "department": "FIST",
            "day_of_week": "Tuesday",
            "start_time": time(10, 0),
            "end_time": time(12, 0),
        },
        {
            "course_code": "FIST103",
            "course_name": "Software Engineering",
            "instructor": "Dr. Ong",
            "quota": 30,
            "credits": 3,
            "semester": "Trimester 1",
            "location": "Room B201",
            "description": "Development lifecycle and tools.",
            "department": "FIST",
            "day_of_week": "Wednesday",
            "start_time": time(14, 0),
            "end_time": time(16, 0),
        },
    ]

    for c in courses_data:
        if not Course.query.filter_by(course_code=c["course_code"]).first():
            course = Course(**c)
            db.session.add(course)

    db.session.commit()

    # === Create sample Enrollments ===
    alice = Student.query.filter_by(email="alice@fist.edu").first()
    daniel = Student.query.filter_by(email="daniel@fist.edu").first()
    fist101 = Course.query.filter_by(course_code="FIST101").first()
    fist102 = Course.query.filter_by(course_code="FIST102").first()

    if alice and fist101:
        if not Enrollment.query.filter_by(student_id=alice.id, course_id=fist101.id).first():
            db.session.add(Enrollment(student_id=alice.id, course_id=fist101.id))

    if daniel and fist102:
        if not Enrollment.query.filter_by(student_id=daniel.id, course_id=fist102.id).first():
            db.session.add(Enrollment(student_id=daniel.id, course_id=fist102.id))

    db.session.commit()
    return "✅ Demo data inserted (Students + Courses + Enrollments)"

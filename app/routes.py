from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_required, current_user
from .forms import StudentRegisterForm, StudentLoginForm
from .models import db, Student, Course, Section
from .models import Course, Enrollment
from .forms import CourseAddForm
from .forms import CourseAddForm, AdminLoginForm
from .forms import CourseEditForm
from .forms import SectionForm
from flask_login import login_user
from flask_login import UserMixin
from flask_login import logout_user
from flask_wtf.csrf import generate_csrf

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
            login_user(student)
            flash("Login successful!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html", form=form)



@main.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_student:
        abort(403)

    student = current_user
    selected_semester = request.args.get('semester')

    # 查询所有课程（可选 semester 过滤）
    course_query = Course.query.filter_by(department=student.department)
    if selected_semester:
        course_query = course_query.filter_by(semester=selected_semester)
    courses = course_query.all()

    # 查询所有可选学期（供下拉菜单用）
    all_semesters = (
        db.session.query(Course.semester)
        .filter_by(department=student.department)
        .distinct()
        .order_by(Course.semester)
        .all()
    )
    all_semesters = [s[0] for s in all_semesters]

    # 已注册的 section ID 和对应课程 ID
    enrolled_section_ids = [e.section_id for e in Enrollment.query.filter_by(student_id=student.id).all()]
    enrolled_section_objs = Section.query.filter(Section.id.in_(enrolled_section_ids)).all()
    enrolled_course_ids = list({s.course_id for s in enrolled_section_objs})

    # 计算当前学分
    enrolled_courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()
    total_credits = sum(c.credits for c in enrolled_courses)

    return render_template(
        "dashboard.html",
        courses=courses,
        enrolled_course_ids=enrolled_course_ids,
        total_credits=total_credits,
        all_semesters=all_semesters,
        selected_semester=selected_semester
    )


@main.route("/enroll/<int:course_id>")
@login_required
def enroll(course_id):
    if not current_user.is_student:
        abort(403)    
    student_id = current_user.id
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
@login_required
def drop(course_id):
    if not current_user.is_student:
        abort(403)
    student_id = current_user.id

    # 找出所有该学生已注册的该课程下的 Section
    enrollments = Enrollment.query.join(Section).filter(
        Enrollment.student_id == student_id,
        Section.course_id == course_id
    ).all()

    if not enrollments:
        flash("You are not enrolled in this course.", "warning")
        return redirect(url_for("main.dashboard"))

    for e in enrollments:
        db.session.delete(e)
    db.session.commit()

    flash("Course and all associated sections dropped.", "info")
    return redirect(url_for("main.dashboard"))


@main.route("/my-courses")
@login_required
def my_courses():
    if not current_user.is_student:
        abort(403)
    student_id = current_user.id
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    sections = [e.section for e in enrollments]

    return render_template("my_courses.html", sections=sections)


@main.route("/logout")
def logout():
    is_student = getattr(current_user, 'is_student', False)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login" if is_student else "main.admin_login"))



from .models import Admin


@main.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)  # ✅ 用 Flask-Login 登录
            flash("Admin login successful!", "success")
            return redirect(url_for("main.admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("admin_login.html", form=form)


@main.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    form = CourseAddForm()
    courses = Course.query.all()

    form.prerequisite_id.choices = [(0, "None")] + [
        (c.id, f"{c.course_code} - {c.course_name}") for c in courses
    ]

    if form.validate_on_submit():
        existing = Course.query.filter_by(course_code=form.course_code.data).first()
        if existing:
            flash("Course code already exists. Please use a unique code.", "danger")
            return redirect(url_for("main.admin_dashboard"))

        prereq_id = form.prerequisite_id.data
        course = Course(
            course_code=form.course_code.data,
            course_name=form.course_name.data,
            credits=form.credits.data,
            semester=form.semester.data,
            department=form.department.data,
            description=form.description.data,
            prerequisite_id=prereq_id if prereq_id != 0 else None 
        )
        db.session.add(course)
        db.session.commit()
        flash("Course added!", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("admin_dashboard.html", form=form, courses=courses)




@main.route("/admin/logout")
def admin_logout():
    logout_user()
    flash("Logged out as admin.", "info")
    return redirect(url_for("main.admin_login"))

@main.route("/admin/delete/<int:course_id>")
@login_required
def admin_delete(course_id):
    if not current_user.is_admin:
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/admin/edit/<int:course_id>", methods=["GET", "POST"])
@login_required
def admin_edit(course_id):
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    form = CourseEditForm(obj=course)

    other_courses = Course.query.filter(Course.id != course.id).all()
    form.prerequisite_id.choices = [(0, "None")] + [
        (c.id, f"{c.course_code} - {c.course_name}") for c in other_courses
    ]
    if request.method == "GET":
        form.prerequisite_id.data = course.prerequisite_id or 0

    if form.validate_on_submit():
        existing = Course.query.filter_by(course_code=form.course_code.data).first()
        if existing and existing.id != course.id:
            flash("Course code already exists.", "danger")
            return redirect(url_for("main.admin_dashboard"))

        # ✅ 先直接更新所有字段，包括 prerequisite_id
        course.course_code = form.course_code.data
        course.course_name = form.course_name.data
        course.credits = form.credits.data
        course.semester = form.semester.data
        course.department = form.department.data
        course.description = form.description.data
        
        # ✅ 这里是正确保存 prerequisite
        if form.prerequisite_id.data == 0:
            course.prerequisite_id = None
        else:
            course.prerequisite_id = form.prerequisite_id.data

        db.session.commit()
        flash("Course updated!", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("course_form.html", form=form, title="Edit Course")


@main.route("/timetable")
@login_required
def timetable():
    student_id = current_user.id
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    sections = [e.section for e in enrollments]

    return render_template("timetable.html", sections=sections)


@main.route("/admin/section/<int:section_id>/students")
@login_required
def admin_view_section_students(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    students = [e.student for e in section.enrollments]
    return render_template("admin_section_students.html", section=section, students=students)




@main.route("/import-sample-data")
def import_sample_data():
    import json
    from datetime import datetime
    from .models import db, Student, Course, Enrollment

    with open("sample_data.json") as f:
        data = json.load(f)

    # === Import Students ===
    for s in data["students"]:
        if not Student.query.filter_by(email=s["email"]).first():
            student = Student(name=s["name"], email=s["email"], department=s["department"])
            student.set_password(s["password"])
            db.session.add(student)

    db.session.commit()

    # === Import Courses ===
    for c in data["courses"]:
        if not Course.query.filter_by(course_code=c["course_code"]).first():
            course = Course(
                course_code=c["course_code"],
                course_name=c["course_name"],
                instructor=c["instructor"],
                quota=c["quota"],
                credits=c["credits"],
                semester=c["semester"],
                location=c["location"],
                description=c["description"],
                department=c["department"],
                day_of_week=c["day_of_week"],
                start_time=datetime.strptime(c["start_time"], "%H:%M:%S").time(),
                end_time=datetime.strptime(c["end_time"], "%H:%M:%S").time()
            )
            db.session.add(course)

    db.session.commit()

    # === Import Enrollments ===
    for e in data["enrollments"]:
        if not Enrollment.query.filter_by(student_id=e["student_id"], course_id=e["course_id"]).first():
            enrollment = Enrollment(student_id=e["student_id"], course_id=e["course_id"])
            db.session.add(enrollment)

    db.session.commit()
    return "✅ Sample data imported from sample_data.json"


@main.route('/admin/section/add', methods=['GET', 'POST'])
@login_required
def admin_add_section():
    if not current_user.is_admin:
        abort(403)

    form = SectionForm()
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}") for c in Course.query.all()]

    if form.validate_on_submit():
        section = Section(
             course_id=form.course_id.data,
             name=form.name.data,
             type=form.type.data,
             instructor=form.instructor.data,
             location=form.location.data,
             day=form.day_of_week.data,
            start_time=form.start_time.data,
             end_time=form.end_time.data,
             quota=form.quota.data
        )
        db.session.add(section)
        db.session.commit()
        flash("Section added!", "success")
        return redirect(url_for('main.admin_dashboard'))

    return render_template('section_form.html', form=form, title="Add New Section")


@main.route('/admin/section/edit/<int:section_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_section(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    form = SectionForm(obj=section)
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}") for c in Course.query.all()]
    form.course_id.data = section.course_id   

    if form.validate_on_submit():
        section.instructor = form.instructor.data
        section.location = form.location.data
        section.day = form.day_of_week.data
        section.start_time = form.start_time.data
        section.end_time = form.end_time.data


        db.session.commit()
        flash("Section updated!", "success")
        return redirect(url_for('main.admin_dashboard'))

    return render_template('section_form.html', form=form, title="Edit Section")

@main.route("/admin/course/<int:course_id>")
@login_required
def admin_course_details(course_id):
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    return render_template("admin_course_details.html", course=course)

@main.route('/admin/section/delete/<int:section_id>')
@login_required
def admin_delete_section(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    course_id = section.course_id
    db.session.delete(section)
    db.session.commit()
    flash("Section deleted.", "info")
    return redirect(url_for('main.admin_course_details', course_id=course_id))

@main.route("/course/<int:course_id>")
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    lecture_sections = Section.query.filter_by(course_id=course_id, type="Lecture").all()
    student_id = current_user.id

    enrolled_section_ids = [e.section_id for e in Enrollment.query.filter_by(student_id=student_id).all()]
    
    # ➡️ 计算当前已修的学分
    enrolled_course_ids = set()
    for enrollment in Enrollment.query.filter_by(student_id=student_id).all():
        if enrollment.section:
            enrolled_course_ids.add(enrollment.section.course_id)
    
    total_credits = db.session.query(db.func.sum(Course.credits)).filter(Course.id.in_(enrolled_course_ids)).scalar() or 0

    return render_template(
        "course_detail.html",
        course=course,
        lectures=lecture_sections,
        enrolled_section_ids=enrolled_section_ids,
        total_credits=total_credits  # ✅ 传进去模板
    )



@main.route("/course/<int:course_id>/select-tutorial")
@login_required
def select_tutorial(course_id):
    lecture_id = request.args.get("lecture_id", type=int)
    if not lecture_id:
        flash("Lecture not selected.", "danger")
        return redirect(url_for("main.dashboard"))

    course = Course.query.get_or_404(course_id)
    tutorial_sections = Section.query.filter(
        Section.course_id == course_id,
        Section.type.in_(["Tutorial", "Lab"])
    ).all()

    student_id = current_user.id
    enrolled_section_ids = [e.section_id for e in Enrollment.query.filter_by(student_id=student_id).all()]
    enrolled_sections = Section.query.filter(Section.id.in_(enrolled_section_ids)).all()

    return render_template("select_tutorial.html",
                        course=course,
                        lecture_id=lecture_id,
                        tutorials=tutorial_sections,
                        enrolled_sections=enrolled_sections,
                        csrf_token=generate_csrf())    


@main.route("/course/<int:course_id>/finalize", methods=["POST"])
@login_required
def finalize_enrollment(course_id):
    lecture_id = request.form.get("lecture_id", type=int)
    tutorial_id = request.form.get("tutorial_id", type=int)
    student_id = current_user.id

    # 获取当前选的课程
    course = Course.query.get_or_404(course_id)

    # ✅ 重复注册检测
    existing = Enrollment.query.join(Section).filter(
        Enrollment.student_id == student_id,
        Section.course_id == course_id
    ).first()
    if existing:
        flash("You already registered this course.", "danger")
        return redirect(url_for("main.dashboard"))

    # ✅ prerequisite 检查
    prereq = course.prerequisite
    if prereq:
        completed_course_ids = [
            s.course_id for s in Enrollment.query.join(Section)
            .filter(Enrollment.student_id == student_id).all()
        ]
        if prereq.id not in completed_course_ids:
            flash(f"Cannot register: Prerequisite {prereq.course_code} - {prereq.course_name} not fulfilled.", "danger")
            return redirect(url_for("main.dashboard"))

    # ✅ 学分上限检查（20 学分）
    current_credits = sum(
        s.course.credits for s in Enrollment.query.join(Section)
        .filter(Enrollment.student_id == student_id).all()
    )
    if current_credits + course.credits > 20:
        flash(f"Cannot register: Credit limit exceeded. You already have {current_credits} credits.", "danger")
        return redirect(url_for("main.dashboard"))

    # 获取两个 section 对象
    lecture = Section.query.get_or_404(lecture_id)
    tutorial = Section.query.get_or_404(tutorial_id)

    # ✅ 时间冲突检测
    enrolled_sections = Enrollment.query.filter_by(student_id=student_id).all()
    for e in enrolled_sections:
        existing_sec = Section.query.get(e.section_id)
        if existing_sec.day == lecture.day:
            if not (lecture.end_time <= existing_sec.start_time or lecture.start_time >= existing_sec.end_time):
                flash(f"Time conflict with {existing_sec.name} (Lecture)", "danger")
                return redirect(url_for("main.dashboard"))
        if existing_sec.day == tutorial.day:
            if not (tutorial.end_time <= existing_sec.start_time or tutorial.start_time >= existing_sec.end_time):
                flash(f"Time conflict with {existing_sec.name} (Tutorial)", "danger")
                return redirect(url_for("main.dashboard"))

    # ✅ 正式注册
    db.session.add(Enrollment(student_id=student_id, section_id=lecture.id))
    db.session.add(Enrollment(student_id=student_id, section_id=tutorial.id))
    db.session.commit()
    flash("Course registered successfully!", "success")
    return redirect(url_for("main.dashboard"))

@main.route("/change_section/<int:section_id>")
@login_required
def change_section(section_id):
    section = Section.query.get_or_404(section_id)
    student_id = current_user.id

    # 删除该课程下旧 Section
    old_enrollments = Enrollment.query.join(Section).filter(
        Enrollment.student_id == student_id,
        Section.course_id == section.course_id,
        Section.type == section.type
    ).all()
    for e in old_enrollments:
        db.session.delete(e)

    # 添加新的 Section
    db.session.add(Enrollment(student_id=student_id, section_id=section.id))
    db.session.commit()
    flash(f"{section.name} updated successfully!", "success")

    return redirect(url_for("main.course_detail", course_id=section.course_id))

@main.route("/init-demo")
def init_demo():
    from datetime import time
    from .models import Student, Course, Section, Enrollment, db

    db.drop_all()
    db.create_all()

    # === Admin Account ===
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)

    # === Students ===
    students = [
        Student(name="Alice Lee", email="alice@student.mmu.edu.my", department="FIST"),
        Student(name="Bob Tan", email="bob@student.mmu.edu.my", department="FIST"),
        Student(name="Chloe Wong", email="chloe@student.mmu.edu.my", department="FIST"),
        Student(name="Daniel Ng", email="daniel@student.mmu.edu.my", department="FCI"),
        Student(name="Eve Lim", email="eve@student.mmu.edu.my", department="FOB"),
    ]
    for s in students:
        s.set_password("123456")
        db.session.add(s)

    db.session.flush()  # 立即写入，方便后续引用 id

    # === Courses & Sections ===
    course1 = Course(
        course_code="FIST101",
        course_name="Introduction to AI",
        credits=3,
        semester="T1",
        department="FIST",
        description="Learn the basics of Artificial Intelligence."
    )
    db.session.add(course1)
    db.session.flush()

    section1 = Section(course_id=course1.id, name="Lec-A1", type="Lecture", instructor="Dr. Ling",
                       location="A101", day="Monday", start_time=time(9, 0), end_time=time(11, 0), quota=30)
    section2 = Section(course_id=course1.id, name="Tut-B1", type="Tutorial", instructor="Ms. Tan",
                       location="B202", day="Tuesday", start_time=time(10, 0), end_time=time(11, 0), quota=20)
    db.session.add_all([section1, section2])

    course2 = Course(
        course_code="FIST102",
        course_name="Data Science Basics",
        credits=3,
        semester="T1",
        department="FIST",
        description="Explore fundamental concepts in data science.",
        prerequisite_id=course1.id  # 设定 prerequisite
    )
    db.session.add(course2)
    db.session.flush()

    section3 = Section(course_id=course2.id, name="Lec-A2", type="Lecture", instructor="Dr. Tan",
                       location="C101", day="Wednesday", start_time=time(9, 0), end_time=time(11, 0), quota=25)
    section4 = Section(course_id=course2.id, name="Lab-C1", type="Lab", instructor="Mr. Lim",
                       location="C203", day="Thursday", start_time=time(14, 0), end_time=time(16, 0), quota=20)
    db.session.add_all([section3, section4])

    course3 = Course(
        course_code="FCI201",
        course_name="Software Engineering Fundamentals",
        credits=4,
        semester="T1",
        department="FCI",
        description="Introduction to software engineering principles."
    )
    db.session.add(course3)
    db.session.flush()

    section5 = Section(course_id=course3.id, name="Lec-B1", type="Lecture", instructor="Dr. Ong",
                       location="E101", day="Thursday", start_time=time(8, 0), end_time=time(10, 0), quota=40)
    db.session.add(section5)

    db.session.commit()
    return "✅ Demo data reset and reinserted!"

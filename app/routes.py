from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort
from flask_login import (
    login_required, login_user, logout_user, current_user, UserMixin
)
from flask_wtf.csrf import generate_csrf

from .models import (
    db, Student, Admin, Course, Section, Enrollment, SystemSetting, CreditTransfer
)
from .forms import (
    StudentRegisterForm, StudentLoginForm, AdminLoginForm,
    CourseAddForm, CourseEditForm, SectionForm, SemesterSettingForm, ForgotPasswordForm, CreditTransferForm
)

from flask import make_response

from .forms import StudentEditForm


main = Blueprint("main", __name__)


# ==================== Shared Start ========================
@main.route("/")
def index():
    return render_template("shared/index.html")

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
    return render_template("shared/register.html", form=form)


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
    return render_template("shared/login.html", form=form)

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
    return render_template("shared/admin_login.html", form=form)


@main.route("/logout")
def logout():
    is_student = getattr(current_user, 'is_student', False)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login" if is_student else "main.admin_login"))

# ==================== Shared End ========================

# ==================== Student Start =======================
# ✅ PATCH 2: Upgraded student dashboard logic for classification

@main.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_student:
        abort(403)

    student = current_user
    student_id = student.id

    # 获取当前开放学期（默认 Term2410）
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Term2410"

    # 获取学生已完成的课程（学期 < 开放学期）
    completed_courses = db.session.query(Course).join(Section).join(Enrollment).filter(
        Enrollment.student_id == student_id,
        Course.semester < open_semester
    ).distinct().all()
    completed_course_ids = {c.id for c in completed_courses}

    # 累计完成的历史学分（无上限）
    total_credits = sum(c.credits for c in completed_courses)

    # 当前学期的所有课程
    all_courses = Course.query.filter_by(department=student.department).all()

    eligible_courses = []
    locked_courses = []
    for course in all_courses:
        if course.id in completed_course_ids:
            continue
        if course.semester != open_semester:
            locked_courses.append((course, "Not offered this semester"))
            continue
        if course.prerequisite and course.prerequisite.id not in completed_course_ids:
            locked_courses.append((course, f"Missing prerequisite: {course.prerequisite.course_code}"))
            continue
        if course.course_name.startswith("FYP") and total_credits < 60:
            locked_courses.append((course, "Requires ≥ 60 credit hours"))
            continue
        eligible_courses.append(course)

    # ✅ 正确：在循环后面计算当前学期的注册学分
    current_enrollments = Enrollment.query.join(Section).join(Course).filter(
        Enrollment.student_id == student_id,
        Course.semester == open_semester
    ).all()

    seen_course_ids = set()
    current_semester_credits = 0
    for e in current_enrollments:
        course = e.section.course
        if course and course.id not in seen_course_ids:
            current_semester_credits += course.credits
            seen_course_ids.add(course.id)




    max_credits = 20  # 可未来配置为 SystemSetting 获取

    # 获取学生已注册的课程 id
    enrolled_section_ids = [e.section_id for e in Enrollment.query.filter_by(student_id=student_id).all()]
    enrolled_section_objs = Section.query.filter(Section.id.in_(enrolled_section_ids)).all()
    enrolled_course_ids = list({s.course_id for s in enrolled_section_objs})

    return render_template("student/dashboard.html",
        eligible_courses=eligible_courses,
        locked_courses=locked_courses,
        completed_courses=completed_courses,
        total_credits=total_credits,
        current_semester_credits=current_semester_credits,
        max_credits=max_credits,
        open_semester=open_semester,
        enrolled_course_ids=enrolled_course_ids
    )


@main.route("/my-courses")
@login_required
def my_courses():
    student_id = current_user.id
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Term2410"

    sections = db.session.query(Section).join(Enrollment).join(Section.course).filter(
        Enrollment.student_id == student_id,
        Course.semester == open_semester
    ).all()

    return render_template("student/my_courses.html", sections=sections, open_semester=open_semester)


@main.route("/timetable")
@login_required
def timetable():
    student_id = current_user.id

    # 获取当前开放学期
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Term2410"

    # 显式 join Section.course 再 filter
    sections = db.session.query(Section).join(Enrollment).join(Section.course).filter(
        Enrollment.student_id == student_id,
        Course.semester == open_semester
    ).all()

    return render_template("student/timetable.html", sections=sections, open_semester=open_semester)



@main.route("/enroll/<int:course_id>")
@login_required
def enroll(course_id):
    if not current_user.is_student:
        abort(403)    
    student_id = current_user.id
    course_to_add = Course.query.get_or_404(course_id)

    # ✅ 已选课程检测
    existing = Enrollment.query.join(Section).filter(
    Enrollment.student_id == student_id,
    Section.course_id == course_id
    ).first()
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

    # 👇 补上计算当前学期学分 & 最大学分
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Term2410"

    current_enrollments = Enrollment.query.join(Section).join(Course).filter(
        Enrollment.student_id == current_user.id,
        Course.semester == open_semester
    ).all()

    # ✅ 避免重复计入相同 course 的 credits
    seen_course_ids = set()
    current_semester_credits = 0
    for e in current_enrollments:
        c = e.section.course  # ✅ 避免覆盖外部的 `course`
        if c and c.id not in seen_course_ids:
            current_semester_credits += c.credits
            seen_course_ids.add(c.id)

    max_credits = 20


    return render_template(
        "student/course_detail.html",
        course=course,
        lectures=lecture_sections,
        enrolled_section_ids=enrolled_section_ids,
        total_credits=total_credits,
        current_semester_credits=current_semester_credits,  # ✅ 新增
        max_credits=max_credits  # ✅ 新增
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

    return render_template("student/select_tutorial.html",
                        course=course,
                        lecture_id=lecture_id,
                        tutorials=tutorial_sections,
                        enrolled_sections=enrolled_sections,
                        csrf_token=generate_csrf())    

@main.route("/profile")
@login_required
def profile():
    if not current_user.is_student:
        abort(403)

    student_id = current_user.id
    student = current_user

    # 当前开放学期
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Term2410"

    # 所有注册记录（含当前和历史）
    enrollments = Enrollment.query.filter_by(student_id=student_id).join(Section).join(Section.course).all()

    completed = []
    current = []
    for e in enrollments:
        course = e.section.course
        if course.semester == open_semester:
            current.append((course, e.section))
        else:
            completed.append((course, e.section))

    # 按课程分组（避免重复）
    completed_grouped = {}
    for course, section in completed:
        if course.id not in completed_grouped:
            completed_grouped[course.id] = {
                "course": course,
                "sections": []
            }
        completed_grouped[course.id]["sections"].append(section)

    total_completed_credits = sum(c["course"].credits for c in completed_grouped.values())

    # ✅ 获取 credit transfer 数据
    credit_transfers = student.credit_transfers
    transfer_credits = sum(ct.credits for ct in credit_transfers)

    total_with_transfer = total_completed_credits + transfer_credits

    return render_template("student/profile.html",
        student=student,
        open_semester=open_semester,
        current_sections=current,
        completed_courses=completed_grouped.values(),
        total_completed_credits=total_completed_credits,
        credit_transfers=credit_transfers,
        transfer_credits=transfer_credits,
        total_with_transfer=total_with_transfer
    )

@main.route("/finance")
@login_required
def finance():
    if not current_user.is_student:
        abort(403)

    student_id = current_user.id

    # 当前开放学期
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Term2410"

    # 获取当前学期的注册课程 Section
    enrollments = Enrollment.query.join(Section).join(Section.course).filter(
        Enrollment.student_id == student_id,
        Course.semester == open_semester
    ).all()

    # 计算每门课程只算一次学费（避免重复 Lecture + Lab）
    seen_course_ids = set()
    tuition_fees = []
    credit_hour_fee = 300
    total_credits = 0

    for e in enrollments:
        course = e.section.course
        if course.id not in seen_course_ids:
            seen_course_ids.add(course.id)
            tuition_fees.append({
                "course": course,
                "credits": course.credits,
                "amount": course.credits * credit_hour_fee
            })
            total_credits += course.credits

    # 动态学费
    tuition_fee = total_credits * credit_hour_fee

    # ✅ 固定费用结构（模仿 MMU 官方网站）
    fixed_fees = {
        "Registration Fee": 250,
        "Activity Fee": 100,
        "Lab/Studio Fee": 100  # 如有 Lab 可启用
    }

    total_fixed_fee = sum(fixed_fees.values())
    total_fee = tuition_fee + total_fixed_fee

    # 奖学金
    scholarship_percentage = current_user.scholarship_percentage or 0
    scholarship_amount = total_fee * (scholarship_percentage / 100)
    net_total = total_fee - scholarship_amount

    return render_template("student/finance.html",
        tuition_fees=tuition_fees,
        fixed_fees=fixed_fees,
        tuition_fee=tuition_fee,
        total_credits=total_credits,
        total_fixed_fee=total_fixed_fee,
        total_fee=total_fee,
        scholarship_percentage=scholarship_percentage,
        scholarship_amount=scholarship_amount,
        net_total=net_total
    )


@main.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        student = Student.query.filter_by(email=email).first()
        if student:
            # ✅ 模拟“发送”邮件
            flash("A password reset link has been sent to your email. Please check your inbox.", "info")
        else:
            flash("Email not found. Please make sure you entered a valid student email.", "danger")
        return redirect(url_for("main.login"))
    return render_template("shared/forgot_password.html", form=form)



#===================== Student End =======================

#===================== Admin Start =======================
from .models import Admin
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

    # 当前开放学期
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Not Set"

    return render_template("admin/dashboard.html", form=form, courses=courses, open_semester=open_semester)


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

    return render_template("admin/course_form.html", form=form, title="Edit Course")

@main.route("/admin/section/<int:section_id>/students")
@login_required
def admin_view_section_students(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    students = [e.student for e in section.enrollments]
    return render_template("admin/section_students.html", section=section, students=students)

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

    return render_template('admin/section_form.html', form=form, title="Add New Section")


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
        section.course_id = form.course_id.data
        section.name = form.name.data
        section.type = form.type.data
        section.instructor = form.instructor.data
        section.location = form.location.data
        section.day = form.day_of_week.data
        section.start_time = form.start_time.data
        section.end_time = form.end_time.data
        section.quota = form.quota.data
        db.session.commit()
        flash("Section updated!", "success")
        return redirect(url_for('main.admin_dashboard'))


    return render_template('admin/section_form.html', form=form, title="Edit Section")

@main.route("/admin/student/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_student(student_id):
    if not current_user.is_admin:
        abort(403)

    student = Student.query.get_or_404(student_id)
    form = StudentEditForm(obj=student)

    if form.validate_on_submit():
        student.name = form.name.data
        student.email = form.email.data
        student.department = form.department.data
        student.scholarship_percentage = form.scholarship_percentage.data
        db.session.commit()
        flash("Student updated!", "success")
        return redirect(url_for("main.admin_all_students"))

    return render_template("admin/edit_student.html", form=form, student=student)


@main.route("/admin/course/<int:course_id>")
@login_required
def admin_course_details(course_id):
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("main.admin_login"))

    course = Course.query.get_or_404(course_id)
    return render_template("admin/course_details.html", course=course)

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


@main.route("/course/<int:course_id>/finalize", methods=["POST"])
@login_required
def finalize_enrollment(course_id):
    lecture_id = request.form.get("lecture_id", type=int)
    tutorial_id = request.form.get("tutorial_id", type=int)
    student_id = current_user.id

    # 获取当前选的课程
    course = Course.query.get_or_404(course_id)

    # ✅ 重复注册检测
# ✅ 是否已注册该课程（无论哪个 section）
    existing_course = Enrollment.query.join(Section).filter(
        Enrollment.student_id == student_id,
        Section.course_id == course_id
    ).first()
    if existing_course:
        flash("You already registered this course.", "danger")
        return redirect(url_for("main.dashboard"))


    # ✅ prerequisite 检查
    prereq = course.prerequisite
    if prereq:
        completed_course_ids = [
            e.section.course_id for e in Enrollment.query.filter_by(student_id=student_id).all()
        ]
        if prereq.id not in completed_course_ids:
            flash(f"Cannot register: Prerequisite {prereq.course_code} - {prereq.course_name} not fulfilled.", "danger")
            return redirect(url_for("main.dashboard"))


    # ✅ 学分上限检查（20 学分）
    current_credits = sum(
        e.section.course.credits for e in Enrollment.query.filter_by(student_id=student_id).all()
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

@main.route("/debug-courses")
def debug_courses():
    output = []
    for code in ["FIST0001", "FIST0002", "FIST0003"]:
        course = Course.query.filter_by(course_code=code).first()
        if course:
            output.append(f"{course.course_code}: ID={course.id}")
        else:
            output.append(f"{code} not found.")
    return "<br>".join(output)

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

@main.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    if not current_user.is_admin:
        abort(403)

    form = SemesterSettingForm()

    # 自动从数据库读取所有不同的学期作为选项
    all_semesters = db.session.query(Course.semester).distinct().all()
    form.semester.choices = [(s[0], s[0]) for s in all_semesters]

    setting = SystemSetting.query.filter_by(key="open_semester").first()
    if request.method == "GET" and setting:
        form.semester.data = setting.value

    if form.validate_on_submit():
        if setting:
            setting.value = form.semester.data
        else:
            setting = SystemSetting(key="open_semester", value=form.semester.data)
            db.session.add(setting)
        db.session.commit()
        flash("Open semester updated!", "success")
        return redirect(url_for("main.admin_settings"))

    return render_template("admin/settings.html", form=form)


@main.route("/admin/students")
@login_required
def admin_all_students():
    if not current_user.is_admin:
        abort(403)
    students = Student.query.all()
    return render_template("admin/all_students.html", students=students)

@main.route("/admin/credit-transfer", methods=["GET", "POST"])
@login_required
def admin_credit_transfer():
    if not current_user.is_admin:
        abort(403)

    form = CreditTransferForm()
    form.student_id.choices = [(s.id, s.name) for s in Student.query.all()]

    if form.validate_on_submit():
        ct = CreditTransfer(
            student_id=form.student_id.data,
            course_code=form.course_code.data,
            course_name=form.course_name.data,
            credits=form.credits.data,
            reason=form.reason.data
        )
        db.session.add(ct)
        db.session.commit()
        flash("Credit transfer record added!", "success")
        return redirect(url_for("main.admin_credit_transfer"))

    transfers = CreditTransfer.query.all()
    return render_template("admin/credit_transfer.html", form=form, transfers=transfers)

#=================== Admin End =======================

#=================== Database Start =======================
@main.route("/init-test-data")
def init_test_data():
    from datetime import time
    db.drop_all()
    db.create_all()

    # Admin
    admin = Admin(username="admin")
    admin.set_password("admin123")
    db.session.add(admin)

    # 3 Students
    students = []
    for i in range(3):
        student = Student(
            name=f"Student {i+1}",
            email=f"student{i+1}@student.mmu.edu.my",
            department="FIST"
        )
        student.set_password("123456")
        db.session.add(student)
        students.append(student)

    db.session.flush()

    # Courses
    courses = []

    c1 = Course(course_code="FIST0001", course_name="Intro to Programming", credits=3,
                semester="Term2410", department="FIST", description="Basic programming")
    db.session.add(c1)
    db.session.flush()
    courses.append(c1)

    c2 = Course(course_code="FIST0002", course_name="Data Structures", credits=3,
                semester="Term2410", department="FIST", description="Has prerequisite", prerequisite_id=c1.id)
    db.session.add(c2)
    db.session.flush()
    courses.append(c2)

    c3 = Course(course_code="FIST0003", course_name="Computer Networks", credits=3,
                semester="Term2410", department="FIST", description="Networking basics")
    db.session.add(c3)
    courses.append(c3)

    c4 = Course(course_code="FIST0004", course_name="FYP Project", credits=6,
                semester="Term2410", department="FIST", description="Final Year Project")
    db.session.add(c4)
    courses.append(c4)

    c5 = Course(course_code="FIST0005", course_name="Operating Systems", credits=3,
                semester="Term2410", department="FIST", description="OS Concepts")
    db.session.add(c5)
    courses.append(c5)

    c6 = Course(course_code="FIST0006", course_name="Software Engineering", credits=3,
                semester="Term2410", department="FIST", description="SE Fundamentals")
    db.session.add(c6)
    courses.append(c6)

    db.session.flush()

    # Add Sections: 1 Lecture + 1 Lab for each
    for course in courses:
        lec = Section(course_id=course.id, name=f"{course.course_code}-LEC", type="Lecture",
                      instructor="Dr. A", location="A101", day="Tuesday",
                      start_time=time(10, 0), end_time=time(12, 0), quota=50)
        lab = Section(course_id=course.id, name=f"{course.course_code}-LAB", type="Lab",
                      instructor="Ms. B", location="B202", day="Wednesday",
                      start_time=time(14, 0), end_time=time(16, 0), quota=30)
        db.session.add(lec)
        db.session.add(lab)

    db.session.flush()

    # Assign some completed courses to students
    # Let student 1 have 60 credits completed (for FYP test)
    for course in courses[:5]:
        lec = Section.query.filter_by(course_id=course.id, type="Lecture").first()
        lab = Section.query.filter_by(course_id=course.id, type="Lab").first()
        db.session.add(Enrollment(student_id=students[0].id, section_id=lec.id))
        db.session.add(Enrollment(student_id=students[0].id, section_id=lab.id))

    # Let student 2 only completed c1 (for prerequisite test)
    lec1 = Section.query.filter_by(course_id=c1.id, type="Lecture").first()
    lab1 = Section.query.filter_by(course_id=c1.id, type="Lab").first()
    db.session.add(Enrollment(student_id=students[1].id, section_id=lec1.id))
    db.session.add(Enrollment(student_id=students[1].id, section_id=lab1.id))

    # student 3 has no completed course (for error cases)
    db.session.flush()

    # System setting
    if not SystemSetting.query.filter_by(key="open_semester").first():
        setting = SystemSetting(key="open_semester", value="Term2410")
        db.session.add(setting)

    db.session.commit()
    return "✅ Test data initialized with 3 students and 6 courses for Term2410."




#http://localhost:5000/init-test-data

@main.route("/debug-enrollments/<int:student_id>")
def debug_enrollments(student_id):
    result = []
    enrollments = Enrollment.query.join(Section).filter(Enrollment.student_id == student_id).all()
    for e in enrollments:
        section = e.section
        course = section.course
        result.append(f"[{course.course_code}] {course.course_name} via {section.name} ({section.type})")
    return "<br>".join(result) or "❌ No enrollments found"
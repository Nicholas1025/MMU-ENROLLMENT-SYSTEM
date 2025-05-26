from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ..models import db, Student, Course, Section, Enrollment, SystemSetting, CreditTransfer
from ..forms import ForgotPasswordForm
from flask_wtf.csrf import generate_csrf

student_bp = Blueprint("student", __name__)
@student_bp.route("/dashboard")
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


@student_bp.route("/my-courses")
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


@student_bp.route("/timetable")
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



@student_bp.route("/enroll/<int:course_id>")
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
        return redirect(url_for("student.dashboard"))

    # ✅ Quota 检查
    current_enrolled = Enrollment.query.filter_by(course_id=course_id).count()
    if current_enrolled >= course_to_add.quota:
        flash("Course quota is full.", "danger")
        return redirect(url_for("student.dashboard"))

    # ✅ 时间冲突检查
    enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.student_id == student_id).all()
    for c in enrolled_courses:
        if c.day_of_week == course_to_add.day_of_week:
            # 先检查双方是否都填了时间
            if all([course_to_add.start_time, course_to_add.end_time, c.start_time, c.end_time]):
                if course_to_add.day_of_week == c.day_of_week:
                    if not (course_to_add.end_time <= c.start_time or course_to_add.start_time >= c.end_time):
                        flash(f"Time conflict with course: {c.course_code}", "danger")
                        return redirect(url_for("student.dashboard"))


    # ✅ 注册课程
    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    flash("Course registered successfully!", "success")
    return redirect(url_for("student.dashboard"))

@student_bp.route("/drop/<int:course_id>")
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
        return redirect(url_for("student.dashboard"))

    for e in enrollments:
        db.session.delete(e)
    db.session.commit()

    flash("Course and all associated sections dropped.", "info")
    return redirect(url_for("student.dashboard"))

@student_bp.route("/course/<int:course_id>")
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

@student_bp.route("/course/<int:course_id>/select-tutorial")
@login_required
def select_tutorial(course_id):
    lecture_id = request.args.get("lecture_id", type=int)
    if not lecture_id:
        flash("Lecture not selected.", "danger")
        return redirect(url_for("student.dashboard"))

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

@student_bp.route("/profile")
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

@student_bp.route("/finance")
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


@student_bp.route("/forgot-password", methods=["GET", "POST"])
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
        return redirect(url_for("student.login"))
    return render_template("shared/forgot_password.html", form=form)


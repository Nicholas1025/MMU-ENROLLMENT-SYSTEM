from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, login_user, logout_user, current_user
from ..models import db, Admin, Course, Section, Enrollment, Student, SystemSetting, CreditTransfer, Instructor
from ..forms import AdminLoginForm, CourseAddForm, CourseEditForm, SectionForm, SemesterSettingForm, StudentEditForm, CreditTransferForm, InstructorEditForm
import os
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("admin.admin_login"))

    form = CourseAddForm()
    courses = Course.query.all()

    form.prerequisite_id.choices = [(0, "None")] + [
        (c.id, f"{c.course_code} - {c.course_name}") for c in courses
    ]

    if form.validate_on_submit():
        existing = Course.query.filter_by(course_code=form.course_code.data).first()
        if existing:
            flash("Course code already exists. Please use a unique code.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

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
        return redirect(url_for("admin.admin_dashboard"))

    # 当前开放学期
    setting = SystemSetting.query.filter_by(key="open_semester").first()
    open_semester = setting.value if setting else "Not Set"

    return render_template("admin/dashboard.html", form=form, courses=courses, open_semester=open_semester)


@admin_bp.route("/admin/logout")
def admin_logout():
    logout_user()
    flash("Logged out as admin.", "info")
    return redirect(url_for("shared.admin_login"))

@admin_bp.route("/admin/delete/<int:course_id>")
@login_required
def admin_delete(course_id):
    if not current_user.is_admin:
        return redirect(url_for("admin.admin_login"))

    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.admin_dashboard"))

@admin_bp.route("/admin/edit/<int:course_id>", methods=["GET", "POST"])
@login_required
def admin_edit(course_id):
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("admin.admin_login"))

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
            return redirect(url_for("admin.admin_dashboard"))

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
        return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin/course_form.html", form=form, title="Edit Course")

@admin_bp.route("/admin/section/<int:section_id>/students")
@login_required
def admin_view_section_students(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    students = [e.student for e in section.enrollments]
    return render_template("admin/section_students.html", section=section, students=students)

@admin_bp.route("/import-sample-data")
def import_sample_data():
    import json
    import os
    from datetime import datetime
    from ..models import db, Student, Course, Section, Enrollment, CreditTransfer

    json_path = os.path.join(os.getcwd(), "sample_data.json")

    if not os.path.exists(json_path):
        return "❌ 找不到 sample_data.json"

    with open(json_path) as f:
        data = json.load(f)

    # === Import Students ===
    for s in data.get("students", []):
        if not Student.query.filter_by(email=s["email"]).first():
            student = Student(
                name=s["name"],
                email=s["email"],
                department=s["department"]
            )
            student.set_password(s["password"])
            db.session.add(student)
    db.session.commit()

        # === Import Instructors ===
    from ..models import Instructor  # 确保导入了 Instructor 模型

    for i in data.get("instructors", []):
        if not Instructor.query.filter_by(email=i["email"]).first():
            instructor = Instructor(
                name=i["name"],
                email=i["email"],
                title=i["title"],
                department=i["department"],
                office=i["office"],
                phone=i["phone"],
                biography=i["biography"],
                profile_pic=i.get("profile_pic")
            )
            instructor.set_password(i["password"])
            db.session.add(instructor)
    db.session.commit()


    # === First pass: Add Courses without prerequisite
    course_map = {}
    for c in data.get("courses", []):
        if not Course.query.filter_by(course_code=c["course_code"]).first():
            course = Course(
                course_code=c["course_code"],
                course_name=c["course_name"],
                credits=c["credits"],
                semester=c["semester"],
                department=c["department"],
                description=c["description"]
            )
            db.session.add(course)
            db.session.flush()
            course_map[c["course_code"]] = course.id
    db.session.commit()

    # === Second pass: Add prerequisites
    for c in data.get("courses", []):
        if "prerequisite_code" in c:
            course = Course.query.filter_by(course_code=c["course_code"]).first()
            prereq = Course.query.filter_by(course_code=c["prerequisite_code"]).first()
            if course and prereq:
                course.prerequisite_id = prereq.id
    db.session.commit()

    # === Import Sections (from JSON) ===
    for s in data.get("sections", []):
        section = Section(
            course_id=s["course_id"],
            name=s["name"],
            type=s["type"],
            location=s["location"],
            day=s["day"],
            start_time=datetime.strptime(s["start_time"], "%H:%M:%S").time(),
            end_time=datetime.strptime(s["end_time"], "%H:%M:%S").time(),
            quota=s["quota"],
            instructor_id=s["instructor_id"]  # ✅ 正确使用 instructor 外键
        )
        db.session.add(section)
    db.session.commit()


    # === Import Enrollments (randomly pick one section for each course)
    for e in data.get("enrollments", []):
        course_sections = Section.query.filter_by(course_id=e["course_id"]).all()
        if not course_sections:
            continue
        selected_section = course_sections[0]  # Pick first section
        exists = Enrollment.query.filter_by(
            student_id=e["student_id"], section_id=selected_section.id
        ).first()
        if not exists:
            enrollment = Enrollment(
                student_id=e["student_id"],
                course_id=e["course_id"],
                section_id=selected_section.id
            )
            db.session.add(enrollment)
    db.session.commit()

    # === Credit Transfers
    for ct in data.get("credit_transfers", []):
        db.session.add(CreditTransfer(
            student_id=ct["student_id"],
            course_code=ct["course_code"],
            course_name=ct["course_name"],
            credits=ct["credits"],
            reason=ct["reason"]
        ))
    db.session.commit()

    return "✅ Sample data successfully imported!"



@admin_bp.route('/admin/section/add', methods=['GET', 'POST'])
@login_required
def admin_add_section():
    if not current_user.is_admin:
        abort(403)

    form = SectionForm()
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}") for c in Course.query.all()]
    form.instructor.choices = [(i.id, f"{i.title or ''} {i.name}") for i in Instructor.query.all()]


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
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/section_form.html', form=form, title="Add New Section")


@admin_bp.route('/admin/section/edit/<int:section_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_section(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    form = SectionForm(obj=section)

    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}") for c in Course.query.all()]
    form.instructor.choices = [(i.id, f"{i.title or ''} {i.name}") for i in Instructor.query.all()]

    form.course_id.data = section.course_id
    form.instructor.data = section.instructor_id  # ✅ 设定默认值

    if form.validate_on_submit():
        section.course_id = form.course_id.data
        section.name = form.name.data
        section.type = form.type.data
        section.instructor_id = form.instructor.data  # ✅ 正确存 instructor_id
        section.location = form.location.data
        section.day = form.day_of_week.data
        section.start_time = form.start_time.data
        section.end_time = form.end_time.data
        section.quota = form.quota.data
        db.session.commit()
        flash("Section updated!", "success")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/section_form.html', form=form, title="Edit Section")


@admin_bp.route("/admin/student/<int:student_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_all_students"))

    return render_template("admin/edit_student.html", form=form, student=student)


@admin_bp.route("/admin/course/<int:course_id>")
@login_required
def admin_course_details(course_id):
    if not current_user.is_admin:
        flash("Admin access only.", "warning")
        return redirect(url_for("admin.admin_login"))

    course = Course.query.get_or_404(course_id)
    return render_template("admin/course_details.html", course=course)

@admin_bp.route('/admin/section/delete/<int:section_id>')
@login_required
def admin_delete_section(section_id):
    if not current_user.is_admin:
        abort(403)

    section = Section.query.get_or_404(section_id)
    course_id = section.course_id
    db.session.delete(section)
    db.session.commit()
    flash("Section deleted.", "info")
    return redirect(url_for('admin.admin_course_details', course_id=course_id))


@admin_bp.route("/course/<int:course_id>/finalize", methods=["POST"])
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
        return redirect(url_for("student.dashboard"))


    # ✅ prerequisite 检查
    prereq = course.prerequisite
    if prereq:
        completed_course_ids = [
            e.section.course_id for e in Enrollment.query.filter_by(student_id=student_id).all()
        ]
        if prereq.id not in completed_course_ids:
            flash(f"Cannot register: Prerequisite {prereq.course_code} - {prereq.course_name} not fulfilled.", "danger")
            return redirect(url_for("student.dashboard"))


    # ✅ 学分上限检查（20 学分）
    current_credits = sum(
        e.section.course.credits for e in Enrollment.query.filter_by(student_id=student_id).all()
    )
    if current_credits + course.credits > 20:
        flash(f"Cannot register: Credit limit exceeded. You already have {current_credits} credits.", "danger")
        return redirect(url_for("student.dashboard"))

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
                return redirect(url_for("student.dashboard"))
        if existing_sec.day == tutorial.day:
            if not (tutorial.end_time <= existing_sec.start_time or tutorial.start_time >= existing_sec.end_time):
                flash(f"Time conflict with {existing_sec.name} (Tutorial)", "danger")
                return redirect(url_for("student.dashboard"))

    # ✅ 正式注册
    db.session.add(Enrollment(student_id=student_id, section_id=lecture.id))
    db.session.add(Enrollment(student_id=student_id, section_id=tutorial.id))
    db.session.commit()
    flash("Course registered successfully!", "success")
    return redirect(url_for("student.dashboard"))

@admin_bp.route("/debug-courses")
def debug_courses():
    output = []
    for code in ["FIST0001", "FIST0002", "FIST0003"]:
        course = Course.query.filter_by(course_code=code).first()
        if course:
            output.append(f"{course.course_code}: ID={course.id}")
        else:
            output.append(f"{code} not found.")
    return "<br>".join(output)

@admin_bp.route("/change_section/<int:section_id>")
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

    return redirect(url_for("student.course_detail", course_id=section.course_id))

@admin_bp.route("/admin/settings", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_settings"))

    return render_template("admin/settings.html", form=form)


@admin_bp.route("/admin/students")
@login_required
def admin_all_students():
    if not current_user.is_admin:
        abort(403)
    students = Student.query.all()
    return render_template("admin/all_students.html", students=students)

@admin_bp.route("/admin/credit-transfer", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_credit_transfer"))

    transfers = CreditTransfer.query.all()
    return render_template("admin/credit_transfer.html", form=form, transfers=transfers)

@admin_bp.route("/instructor/<int:id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_instructor(id):
    if not current_user.is_admin:
        abort(403)

    instructor = Instructor.query.get_or_404(id)
    form = InstructorEditForm(obj=instructor)

    if form.validate_on_submit():
        instructor.name = form.name.data
        instructor.email = form.email.data
        instructor.title = form.title.data
        instructor.department = form.department.data
        instructor.phone = form.phone.data
        instructor.office = form.office.data
        instructor.biography = form.biography.data

        if form.password.data:
            instructor.set_password(form.password.data)

        # 处理头像
        if form.profile_pic.data:
            filename = secure_filename(form.profile_pic.data.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join("app/static/uploads", unique_filename)
            form.profile_pic.data.save(filepath)
            instructor.profile_pic = unique_filename

        db.session.commit()
        flash("Instructor updated successfully!", "success")
        return redirect(url_for("admin.admin_all_instructors"))

    return render_template("admin/edit_instructor.html", form=form, instructor=instructor)

@admin_bp.route("/admin/instructors")
@login_required
def admin_instructor_list():
    if not current_user.is_admin:
        abort(403)

    instructors = Instructor.query.all()
    return render_template("admin/instructor_list.html", instructors=instructors)

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, Instructor, Section, Enrollment, Student
from ..forms import InstructorLoginForm, InstructorProfileForm
from werkzeug.utils import secure_filename
import os

instructor_bp = Blueprint("instructor", __name__, url_prefix="/instructor")

@instructor_bp.route("  ", methods=["GET", "POST"])
def instructor_login():
    form = InstructorLoginForm()
    if form.validate_on_submit():
        instructor = Instructor.query.filter_by(email=form.email.data).first()
        if instructor and instructor.check_password(form.password.data):
            login_user(instructor)
            flash("Instructor login successful!", "success")
            return redirect(url_for("instructor.dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("instructor/login.html", form=form)

@instructor_bp.route("/login", methods=["GET", "POST"])
def login():
    form = InstructorLoginForm()
    if form.validate_on_submit():
        instructor = Instructor.query.filter_by(email=form.email.data).first()
        if instructor and instructor.check_password(form.password.data):
            login_user(instructor)
            flash("Instructor login successful!", "success")
            return redirect(url_for("instructor.dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("instructor/login.html", form=form)

@instructor_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if not current_user.is_instructor:
        abort(403)

    form = InstructorProfileForm()
    instructor = current_user

    if form.validate_on_submit():
        file = form.profile_pic.data
        if file:
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1]
            new_filename = f"instructor_{instructor.id}{ext}"
            upload_path = os.path.join(current_app.static_folder, "uploads", new_filename)

            # 删除旧文件（如存在）
            if instructor.profile_pic:
                try:
                    old_path = os.path.join(current_app.static_folder, "uploads", instructor.profile_pic)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except:
                    pass

            file.save(upload_path)
            instructor.profile_pic = new_filename
            db.session.commit()
            flash("Profile picture updated!", "success")
            return redirect(url_for("instructor.profile"))

    return render_template("instructor/profile.html", instructor=instructor, form=form)

@instructor_bp.route("/timetable")
@login_required
def timetable():
    if not current_user.is_instructor:
        abort(403)

    sections = Section.query.filter_by(instructor=current_user.name).all()

    return render_template("instructor/timetable.html", sections=sections)

@instructor_bp.route("/sections")
@login_required
def sections():
    if not current_user.is_instructor:
        abort(403)

    sections = Section.query.filter_by(instructor=current_user.name).all()
    return render_template("instructor/sections.html", sections=sections)

@instructor_bp.route("/section/<int:section_id>/students")
@login_required
def section_students(section_id):
    if not current_user.is_instructor:
        abort(403)

    section = Section.query.get_or_404(section_id)
    if section.instructor != current_user.name:
        abort(403)

    students = [e.student for e in section.enrollments]
    return render_template("instructor/section_students.html", section=section, students=students)

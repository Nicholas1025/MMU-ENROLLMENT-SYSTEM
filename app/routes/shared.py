from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from ..models import db, Student, Admin
from ..forms import StudentRegisterForm, StudentLoginForm, AdminLoginForm

shared = Blueprint("shared", __name__)

@shared.route("/")
def index():
    return render_template("shared/index.html")

@shared.route("/register", methods=["GET", "POST"])
def register():
    form = StudentRegisterForm()
    if form.validate_on_submit():
        existing = Student.query.filter_by(email=form.email.data).first()
        if existing:
            flash("Email already registered.", "warning")
            return redirect(url_for("shared.register"))

        student = Student(
            name=form.name.data,
            email=form.email.data,
            department=form.department.data
        )
        student.set_password(form.password.data)
        db.session.add(student)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for("shared.login"))
    return render_template("shared/register.html", form=form)

@shared.route("/login", methods=["GET", "POST"])
def login():
    form = StudentLoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data).first()
        if student and student.check_password(form.password.data):
            login_user(student)
            flash("Login successful!", "success")
            return redirect(url_for("student.dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("shared/login.html", form=form)

@shared.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash("Admin login successful!", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("shared/admin_login.html", form=form)

@shared.route("/logout")
def logout():
    is_student = getattr(current_user, 'is_student', False)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("shared.login" if is_student else "shared.admin_login"))
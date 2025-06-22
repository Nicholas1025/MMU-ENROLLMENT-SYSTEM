from flask import Flask, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from .models import db, Admin, Student, Instructor

from .routes.student import student_bp
from .routes.admin import admin_bp
from .routes.shared import shared
from .routes.instructor import instructor_bp

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    csrf.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "shared.login"  

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("student-"):
            return Student.query.get(int(user_id.split("-")[1]))
        elif user_id.startswith("instructor-"):
            return Instructor.query.get(int(user_id.split("-")[1]))
        elif user_id.startswith("admin-"):
            return Admin.query.get(int(user_id.split("-")[1]))
        return None


    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/admin"):
            return redirect(url_for("shared.admin_login"))
        elif request.path.startswith("/instructor"):
            return redirect(url_for("instructor.login"))
        return redirect(url_for("shared.login"))

    app.register_blueprint(shared)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(instructor_bp)

    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    return app

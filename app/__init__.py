from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from .models import db, Admin, Student
from .routes import main

csrf = CSRFProtect()  # ✅ 先声明 CSRF 对象

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    csrf.init_app(app)  # ✅ 正确绑定 CSRF 到 app 上

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "main.admin_login"
    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id)) or Student.query.get(int(user_id))



    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/admin"):
            return redirect(url_for("main.admin_login"))
        return redirect(url_for("main.login"))


    app.register_blueprint(main)

    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    return app

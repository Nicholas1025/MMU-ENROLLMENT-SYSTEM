from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from .models import db, Admin  # ✅ 正确：从 models.py 引入 db 实例

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    CSRFProtect(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

        # 可选：自动添加默认 admin
        if not Admin.query.first():
            admin = Admin(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    return app

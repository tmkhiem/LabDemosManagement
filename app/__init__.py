from flask import Flask, render_template

from config import config

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    from .student import student_bp
    from .proxy import proxy_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(proxy_bp)

    # Register CLI commands
    from . import cli as cli_module
    cli_module.register_commands(app)

    # Custom 404 handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    # Public index
    @app.route("/")
    def index():
        from .models import Demo, User

        students = (
            User.query.filter_by(role="student", is_active=True)
            .order_by(User.display_name)
            .all()
        )
        demos_by_student = {}
        for student in students:
            active_demos = student.demos.filter_by(is_active=True).all()
            if active_demos:
                demos_by_student[student] = active_demos
        return render_template("index.html", demos_by_student=demos_by_student)

    return app


from flask import Flask, flash, redirect, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_wtf.csrf import CSRFError, CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from config import Config
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to see that page."

@event.listens_for(Engine, "connect")
def enable_foreign_keys(connection, record):
    if connection.__class__.__module__.startswith("sqlite3"):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    if app.config["SECRET_KEY"] == "dev-change-me" and not app.config.get("TESTING"):
        app.logger.warning("SECRET_KEY is the default. Set SECRET_KEY in .env before deploying.")

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        flash("That form expired. Please try again.")
        return redirect(request.referrer or "/")

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    with app.app_context():
        from app import models
        db.create_all()

        if app.config.get("SEED_SAMPLE_RECIPES"):
            from app.recipes import seed_sample_recipes
            seed_sample_recipes()

    from app.routes import main
    app.register_blueprint(main)

    from app.auth import auth, create_user_command
    app.register_blueprint(auth)
    app.cli.add_command(create_user_command)

    from app.importer import import_recipes_command
    app.cli.add_command(import_recipes_command)

    return app

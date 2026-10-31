
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
login_manager = LoginManager()
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

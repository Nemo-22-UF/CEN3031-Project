
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

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

    with app.app_context():
        from app import models
        db.create_all()

    from app.routes import main
    app.register_blueprint(main)

    from app.importer import import_recipes_command
    app.cli.add_command(import_recipes_command)

    return app

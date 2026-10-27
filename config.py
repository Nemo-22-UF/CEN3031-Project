import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    # Load the sample recipes into an empty database on startup.
    SEED_SAMPLE_RECIPES = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Tests start empty and seed only when they need recipes.
    SEED_SAMPLE_RECIPES = False

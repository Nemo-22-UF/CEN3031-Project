import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")

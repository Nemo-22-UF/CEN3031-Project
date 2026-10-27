import pytest

from app import create_app
from config import TestConfig


@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    from app.recipes import seed_sample_recipes

    with app.app_context():
        seed_sample_recipes()
    return app.test_client()

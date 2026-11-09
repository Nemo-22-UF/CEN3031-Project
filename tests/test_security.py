import pytest

from app import create_app, db
from app.models import User
from config import TestConfig


class CsrfConfig(TestConfig):
    WTF_CSRF_ENABLED = True


class LimitConfig(TestConfig):
    RATELIMIT_ENABLED = True
    LOGIN_ATTEMPT_LIMIT = "3 per minute"


def make_user(app, username="cook", password="password123"):
    with app.app_context():
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


def test_forms_include_csrf_token():
    client = create_app(CsrfConfig).test_client()
    for page in ["/login", "/register"]:
        assert 'name="csrf_token"' in client.get(page).get_data(as_text=True)


def test_post_without_csrf_token_is_rejected():
    app = create_app(CsrfConfig)
    make_user(app)
    client = app.test_client()
    response = client.post("/login", data={"username": "cook", "password": "password123"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_login_locks_after_too_many_failures():
    app = create_app(LimitConfig)
    make_user(app)
    client = app.test_client()
    for _ in range(3):
        assert client.post("/login", data={"username": "cook", "password": "wrong"}).status_code == 400
    blocked = client.post("/login", data={"username": "cook", "password": "password123"})
    assert blocked.status_code == 429
    assert "Too many failed attempts" in blocked.get_data(as_text=True)


def test_successful_logins_do_not_count():
    app = create_app(LimitConfig)
    make_user(app)
    client = app.test_client()
    for _ in range(5):
        assert client.post("/login", data={"username": "cook", "password": "password123"}).status_code == 302
        client.post("/logout")


def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_user_text_is_escaped(app, client):
    make_user(app, "cook", "password123")
    client.post("/login", data={"username": "cook", "password": "password123"})
    html = client.get("/recipes?q=<script>alert(1)</script>").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html

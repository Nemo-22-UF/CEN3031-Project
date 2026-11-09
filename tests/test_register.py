"""Account registration (PBI-04)."""

import pytest

from app import db
from app.models import User


def register(client, username="maria", password="secret123", confirm=None):
    return client.post(
        "/register",
        data={"username": username, "password": password, "confirm": password if confirm is None else confirm},
    )


def add_user(app, username="maria", password="secret123"):
    with app.app_context():
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


def test_register_page_loads(client):
    response = client.get("/register")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Create an account" in html
    assert 'name="confirm"' in html


def test_login_page_links_to_register(client):
    html = client.get("/login").get_data(as_text=True)
    assert 'href="/register"' in html


def test_nav_shows_sign_up_only_when_logged_out(app, client):
    assert 'href="/register">Sign up<' in client.get("/").get_data(as_text=True)
    register(client)
    assert "Sign up" not in client.get("/").get_data(as_text=True)


def test_register_page_links_back_to_login(client):
    html = client.get("/register").get_data(as_text=True)
    assert 'href="/login"' in html


def test_valid_registration_logs_in_and_goes_to_recipes(app, client):
    response = register(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/recipes")

    html = client.get("/recipes").get_data(as_text=True)
    assert "Welcome, maria! Your account is ready." in html
    assert "<h1>maria" in client.get("/profile").get_data(as_text=True)

    with app.app_context():
        user = User.query.filter_by(username="maria").one()
        assert not user.is_admin
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")


def test_new_account_can_log_in_again(app, client):
    register(client)
    client.post("/logout")
    response = client.post("/login", data={"username": "maria", "password": "secret123"})
    assert response.headers["Location"].endswith("/profile")


def test_taken_username_shows_error(app, client):
    add_user(app)
    response = register(client, password="different1")
    assert response.status_code == 400
    assert "That username is taken" in response.get_data(as_text=True)
    with app.app_context():
        assert User.query.count() == 1


def test_taken_username_ignores_case(app, client):
    add_user(app)
    response = register(client, username="Maria")
    assert response.status_code == 400
    assert "That username is taken" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "username, password, confirm, message",
    [
        ("", "secret123", "secret123", "Fill in every field"),
        ("maria", "", "", "Fill in every field"),
        ("maria", "secret123", "", "Fill in every field"),
        ("ab", "secret123", "secret123", "3 to 30 characters"),
        ("a" * 31, "secret123", "secret123", "3 to 30 characters"),
        ("bad name!", "secret123", "secret123", "letters, numbers and underscores"),
        ("maria", "short", "short", "at least 8 characters"),
        ("maria", "secret123", "secret124", "don&#39;t match"),
    ],
)
def test_invalid_registration_shows_error(app, client, username, password, confirm, message):
    response = register(client, username, password, confirm)
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    with app.app_context():
        assert User.query.count() == 0


def test_failed_registration_keeps_username_but_not_password(client):
    html = register(client, "maria", "secret123", "nope").get_data(as_text=True)
    assert 'value="maria"' in html
    assert "secret123" not in html


def test_signed_in_user_skips_register_page(app, client):
    register(client)
    response = client.get("/register")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

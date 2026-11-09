"""Login, logout, and route protection (PBI-05)."""

import pytest

from app import db
from app.models import User


def add_user(app, username="maria", password="secret123", is_admin=False):
    with app.app_context():
        user = User(username=username, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


def log_in(client, username="maria", password="secret123", next_url=None):
    url = "/login" if next_url is None else f"/login?next={next_url}"
    return client.post(url, data={"username": username, "password": password})


def test_password_is_hashed_not_stored(app):
    add_user(app)
    with app.app_context():
        user = User.query.filter_by(username="maria").one()
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")
        assert not user.check_password("wrong")


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Log in" in response.get_data(as_text=True)


def test_valid_login_goes_to_profile(app, client):
    add_user(app)
    response = log_in(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    html = client.get("/profile").get_data(as_text=True)
    assert "<h1>maria" in html
    assert "Log out" in html


@pytest.mark.parametrize(
    "username, password",
    [("maria", "wrong"), ("nobody", "secret123"), ("", "secret123"), ("maria", "")],
)
def test_bad_login_shows_error(app, client, username, password):
    add_user(app)
    response = log_in(client, username, password)
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "username and password" in html or "Incorrect username or password" in html
    assert client.get("/profile").status_code == 302


def test_logout_ends_the_session(app, client):
    add_user(app)
    log_in(client)
    response = client.post("/logout")
    assert response.status_code == 302
    assert client.get("/profile").status_code == 302


def test_logout_needs_a_post(app, client):
    add_user(app)
    log_in(client)
    assert client.get("/logout").status_code == 405
    assert client.get("/profile").status_code == 200


def test_profile_redirects_to_login_when_signed_out(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login?next=%2Fprofile" in response.headers["Location"]


def test_login_returns_to_the_page_you_asked_for(app, client):
    add_user(app, is_admin=True)
    response = log_in(client, next_url="/admin")
    assert response.headers["Location"].endswith("/admin")


def test_login_ignores_next_links_to_other_sites(app, client):
    add_user(app)
    response = log_in(client, next_url="https://evil.example.com")
    assert response.headers["Location"].endswith("/profile")
    response = client.post("/logout")
    response = log_in(client, next_url="//evil.example.com")
    assert response.headers["Location"].endswith("/profile")


def test_admin_page_blocks_members(app, client):
    add_user(app)
    log_in(client)
    assert client.get("/admin").status_code == 403


def test_admin_page_allows_admins(app, client):
    add_user(app, username="chef", is_admin=True)
    log_in(client, username="chef")
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Only admins can see this page" in response.get_data(as_text=True)


def test_admin_page_redirects_when_signed_out(client):
    assert client.get("/admin").status_code == 302


def test_nav_shows_login_or_username(app, client):
    add_user(app)
    assert "Log in" in client.get("/").get_data(as_text=True)
    log_in(client)
    assert "maria" in client.get("/").get_data(as_text=True)


def test_logged_in_user_skips_login_page(app, client):
    add_user(app)
    log_in(client)
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_usernames_are_unique(app):
    add_user(app)
    with pytest.raises(Exception):
        add_user(app)


def test_create_user_command(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["create-user", "chef", "--admin", "--password", "pass1234"])
    assert "Created admin 'chef'" in result.output
    with app.app_context():
        user = User.query.filter_by(username="chef").one()
        assert user.is_admin
        assert user.check_password("pass1234")

    again = runner.invoke(args=["create-user", "chef", "--password", "pass1234"])
    assert again.exit_code != 0
    assert "already exists" in again.output

from functools import wraps

import re

import click
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask.cli import with_appcontext
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from app import db, limiter, login_manager
from app.models import User

auth = Blueprint("auth", __name__)

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
MIN_PASSWORD_LENGTH = 8


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view):
    """Only let signed-in admins through. Members get a 403."""
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def safe_next(target):
    # Only follow redirects back into this site, never to another domain.
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("auth.profile")


@auth.app_errorhandler(429)
def too_many_attempts(error):
    if request.endpoint != "auth.login":
        return error
    return render_template(
        "login.html",
        error="Too many failed attempts. Wait a minute and try again.",
        username=request.form.get("username", "").strip(),
    ), 429


def login_limit():
    return current_app.config.get("LOGIN_ATTEMPT_LIMIT", "5 per minute")


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit(
    login_limit,
    methods=["POST"],
    deduct_when=lambda response: response.status_code != 302,
)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))

    error = None
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not username or not password:
            error = "Enter your username and password."
        elif user is None or not user.check_password(password):
            error = "Incorrect username or password."
        else:
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(safe_next(request.args.get("next")))

    return render_template("login.html", error=error, username=username), (400 if error else 200)


def registration_error(username, password, confirm):
    """Return a message explaining what's wrong with the form, or None if it's valid."""
    if not username or not password or not confirm:
        return "Fill in every field."
    if not USERNAME_PATTERN.match(username):
        return "Usernames are 3 to 30 characters: letters, numbers and underscores only."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Passwords need at least {MIN_PASSWORD_LENGTH} characters."
    if password != confirm:
        return "The passwords don't match."
    # Treat "Max" and "max" as the same name so people can't be confused for each other.
    if User.query.filter(func.lower(User.username) == username.lower()).first():
        return "That username is taken. Try another one."
    return None


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.profile"))

    error = None
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = registration_error(username, password, confirm)

        if error is None:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Welcome, {user.username}! Your account is ready.")
            return redirect(url_for("main.recipes"))

    return render_template(
        "register.html", error=error, username=username, min_password_length=MIN_PASSWORD_LENGTH
    ), (400 if error else 200)


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@auth.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@auth.route("/admin")
@admin_required
def admin():
    # The admin tools themselves come later (PBI-17 and PBI-18). This page proves the gate works.
    return render_template("admin.html")


@click.command("create-user")
@click.argument("username")
@click.option("--admin", is_flag=True, help="Give this user admin access.")
@click.password_option()
@with_appcontext
def create_user_command(username, admin, password):
    """Create an account from the command line, e.g. an admin account."""
    if User.query.filter_by(username=username).first():
        raise click.ClickException(f"User '{username}' already exists.")
    user = User(username=username, is_admin=admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Created {'admin' if admin else 'user'} '{username}'.")

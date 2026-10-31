from functools import wraps

import click
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask.cli import with_appcontext
from flask_login import current_user, login_required, login_user, logout_user

from app import db, login_manager
from app.models import User

auth = Blueprint("auth", __name__)


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


@auth.route("/login", methods=["GET", "POST"])
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
    # The admin tools themselves come later (PBI-15). This page proves the gate works.
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

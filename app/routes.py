from flask import Blueprint, abort, redirect, render_template, request, url_for
from app.recipes import get_all_recipes, get_recipe, search_recipes
from app.servings import (
    MAX_SERVINGS,
    MIN_SERVINGS,
    format_quantity,
    format_unit,
    parse_servings,
    scale_ingredients,
)
from flask_login import current_user, login_required
from app import db
import secrets
from sqlalchemy.exc import IntegrityError
from app.models import Completion, Favorite, get_favorites, RecipeProgress

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/health")
def health():
    return {"status": "ok"}


@main.route("/recipes")
def recipes():
    query = request.args.get("q", "").strip()
    if query:
        found = search_recipes(query)
    else:
        found = get_all_recipes()
    favorite_ids = set()
    if current_user.is_authenticated:
        favorite_ids = {favorite.recipe_id for favorite in get_favorites(current_user.id)}
    progress_status = {}
    if current_user.is_authenticated:
        progress_records = RecipeProgress.query.filter_by(user_id=current_user.id).all()
        progress_status = {record.recipe_id: record.status for record in progress_records}
    return render_template("recipes.html", recipes=found, query=query,favorite_ids = favorite_ids, progress_status = progress_status)

@main.route("/recipes/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)
    is_favorite = (
        current_user.is_authenticated
        and Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first() is not None
    )
    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        format_quantity=format_quantity,
        format_unit=format_unit,
        is_favorite=is_favorite,
    )

@main.route("/recipes/<int:recipe_id>/cook")
def cook(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)
    total_steps = len(recipe["steps"])
    step = request.args.get("step", default=1, type=int)
    servings, servings_error = parse_servings(request.args.get("servings"), recipe["base_servings"])
    if step < 1 or step > total_steps:
        clamped = min(max(step, 1), total_steps)
        return redirect(url_for("main.cook", recipe_id=recipe_id, step=clamped, servings=servings))
    ingredients = scale_ingredients(recipe["ingredients"], recipe["base_servings"], servings)
    token = secrets.token_hex(16)
    if current_user.is_authenticated:
        progress = RecipeProgress.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
        if not progress:
            progress = RecipeProgress(user_id=current_user.id, recipe_id=recipe_id, current_step=step)
            db.session.add(progress)
        else:
            progress.current_step = step
        progress.status= "started"
        db.session.commit()
    return render_template(
        "cook.html",
        recipe=recipe,
        step=step,
        total_steps=total_steps,
        instruction=recipe["steps"][step - 1],
        servings=servings,
        servings_error=servings_error,
        min_servings=MIN_SERVINGS,
        max_servings=MAX_SERVINGS,
        ingredients=ingredients,
        format_quantity=format_quantity,
        format_unit=format_unit,
        token=token,
    ), (400 if servings_error else 200)


@main.route("/recipes/<int:recipe_id>/cook/complete")
def cook_complete(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)
    if current_user.is_authenticated:
        progress = RecipeProgress.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
        if progress is None:
            progress = RecipeProgress(user_id=current_user.id, recipe_id=recipe_id, current_step=len(recipe["steps"]))
            db.session.add(progress)
        progress.status = "finished"
        progress.current_step = len(recipe["steps"])
        db.session.commit()
    return render_template("cook_complete.html", recipe=recipe)

@main.route("/recipes/<int:recipe_id>/cook/save", methods=["POST"])
@login_required
def save_completion(recipe_id):
    if get_recipe(recipe_id) is None:
        abort(404)
    token = request.form.get("token")
    if not token:
        abort(400)
    existing = Completion.query.filter_by(submission_token=token).first()
    if existing:
        if existing.user_id != current_user.id or existing.recipe_id != recipe_id:
            abort(403)
    else:
        db.session.add(Completion(
            user_id=current_user.id,
            recipe_id=recipe_id,
            submission_token=token
        ))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            existing = Completion.query.filter_by(submission_token=token).first()
            if existing is None:
                raise
            if existing.user_id != current_user.id or existing.recipe_id != recipe_id:
                abort(403)

    return redirect(url_for("main.cook_complete", recipe_id=recipe_id))


@main.route("/recipes/<int:recipe_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(recipe_id):
    if get_recipe(recipe_id) is None:
        abort(404)
    favorite = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if favorite:
        db.session.delete(favorite)
    else:
        db.session.add(Favorite(user_id=current_user.id, recipe_id=recipe_id))
    db.session.commit()
    next_page = request.form.get("next", "")
    if next_page.startswith("/") and not next_page.startswith("//"):
        return redirect(next_page)
    return redirect(url_for("main.recipe_detail", recipe_id=recipe_id))


@main.route("/favorites")
@login_required
def favorites():
    recipes = [get_recipe(favorite.recipe_id) for favorite in get_favorites(current_user.id)]
    return render_template("favorites.html", recipes=[recipe for recipe in recipes if recipe])

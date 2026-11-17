"""Admin tools for adding, editing and deleting recipes (PBI-17 and PBI-18).

Every route here is admin only. Members get a 403 and signed-out users are
sent to the login page, the same as the /admin page.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from app import db
from app.auth import admin_required
from app.importer import parse_measure
from app.models import Completion, CookingStep, Favorite, Ingredient, Recipe, RecipeIngredient
from app.servings import MAX_SERVINGS, MIN_SERVINGS

admin = Blueprint("admin", __name__, url_prefix="/admin/recipes")

MAX_TITLE = 100
MAX_ITEMS = 30
MAX_INGREDIENT = 100
MAX_STEP = 500

# Words that count as a unit when they come right after the amount,
# so "2 tbsp butter" is (2, "tbsp", "butter") but "2 eggs" is (2, "", "eggs").
UNITS = {
    "tsp", "tbsp", "cup", "cups", "oz", "lb", "lbs", "g", "kg", "ml", "l",
    "slice", "slices", "clove", "cloves", "can", "cans", "pinch", "pinches",
}


def parse_ingredient(line):
    """Turn "2 tbsp butter" into {"quantity": 2.0, "unit": "tbsp", "name": "butter"}.

    A line with no amount, like "Salt, to taste", gets quantity None.
    """
    measure = parse_measure(line)
    if measure is None:
        return {"quantity": None, "unit": "", "name": line}

    quantity, rest = measure
    unit, _, name = rest.partition(" ")
    if unit.lower() not in UNITS:
        unit, name = "", rest
    return {"quantity": quantity, "unit": unit.lower(), "name": name.strip()}


def lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def check_recipe_form(form, recipe_id=None):
    """Return (recipe_data, error). error is None when the form is valid."""
    title = form.get("title", "").strip()
    servings_text = form.get("servings", "").strip()
    ingredient_lines = lines(form.get("ingredients", ""))
    steps = lines(form.get("steps", ""))

    if not 3 <= len(title) <= MAX_TITLE:
        return None, f"The title must be 3 to {MAX_TITLE} characters."
    duplicate = Recipe.query.filter(func.lower(Recipe.name) == title.lower())
    if recipe_id is not None:
        duplicate = duplicate.filter(Recipe.id != recipe_id)
    if duplicate.first():
        return None, "A recipe with that title already exists."

    if not servings_text.isdigit() or not MIN_SERVINGS <= int(servings_text) <= MAX_SERVINGS:
        return None, f"Servings must be a whole number from {MIN_SERVINGS} to {MAX_SERVINGS}."

    if not 1 <= len(ingredient_lines) <= MAX_ITEMS:
        return None, f"Add 1 to {MAX_ITEMS} ingredients, one per line."
    if not 1 <= len(steps) <= MAX_ITEMS:
        return None, f"Add 1 to {MAX_ITEMS} steps, one per line."
    if any(len(line) > MAX_INGREDIENT for line in ingredient_lines):
        return None, f"Each ingredient line can be up to {MAX_INGREDIENT} characters."
    if any(len(step) > MAX_STEP for step in steps):
        return None, f"Each step can be up to {MAX_STEP} characters."

    ingredients = [parse_ingredient(line) for line in ingredient_lines]
    if any(not item["name"] for item in ingredients):
        return None, "Every ingredient needs a name after the amount."
    names = [item["name"].lower() for item in ingredients]
    if len(names) != len(set(names)):
        return None, "Each ingredient can only be listed once."

    return {"title": title, "servings": int(servings_text), "ingredients": ingredients, "steps": steps}, None


def save_recipe(recipe, data):
    """Copy the checked form data onto a new or existing recipe and commit."""
    recipe.name = data["title"]
    recipe.base_servings = data["servings"]

    recipe.ingredients.clear()
    recipe.steps.clear()
    db.session.flush()

    for item in data["ingredients"]:
        ingredient = Ingredient.query.filter(func.lower(Ingredient.name) == item["name"].lower()).first()
        if ingredient is None:
            ingredient = Ingredient(name=item["name"])
        recipe.ingredients.append(RecipeIngredient(ingredient=ingredient, quantity=item["quantity"], unit=item["unit"]))
    for number, instruction in enumerate(data["steps"], start=1):
        recipe.steps.append(CookingStep(step_number=number, instruction=instruction))

    db.session.add(recipe)
    db.session.commit()
    return recipe


def delete_recipe(recipe):
    """Delete a recipe along with the favorites and completions that point to it."""
    Favorite.query.filter_by(recipe_id=recipe.id).delete()
    Completion.query.filter_by(recipe_id=recipe.id).delete()
    db.session.delete(recipe)
    db.session.commit()


def form_values(recipe):
    """Turn a saved recipe back into the text the form shows."""
    def ingredient_line(item):
        if item.quantity is None:
            return item.ingredient.name
        amount = f"{item.quantity:g}"
        return " ".join(part for part in (amount, item.unit, item.ingredient.name) if part)

    return {
        "title": recipe.name,
        "servings": recipe.base_servings,
        "ingredients": "\n".join(ingredient_line(item) for item in recipe.ingredients),
        "steps": "\n".join(step.instruction for step in recipe.steps),
    }


def get_recipe_or_404(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        abort(404)
    return recipe


@admin.route("/")
@admin_required
def recipe_list():
    recipes = Recipe.query.order_by(Recipe.name).all()
    return render_template("admin_recipes.html", recipes=recipes)


@admin.route("/new", methods=["GET", "POST"])
@admin_required
def new_recipe():
    values, error = {"title": "", "servings": 2, "ingredients": "", "steps": ""}, None
    if request.method == "POST":
        values = request.form
        data, error = check_recipe_form(request.form)
        if error is None:
            recipe = save_recipe(Recipe(), data)
            flash(f"Added {recipe.name}.")
            return redirect(url_for("admin.recipe_list"))
    return render_template("admin_recipe_form.html", heading="Add a recipe", values=values, error=error), (400 if error else 200)


@admin.route("/<int:recipe_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_recipe(recipe_id):
    recipe = get_recipe_or_404(recipe_id)
    values, error = form_values(recipe), None
    if request.method == "POST":
        values = request.form
        data, error = check_recipe_form(request.form, recipe_id=recipe.id)
        if error is None:
            save_recipe(recipe, data)
            flash(f"Saved changes to {recipe.name}.")
            return redirect(url_for("admin.recipe_list"))
    return render_template("admin_recipe_form.html", heading=f"Edit {recipe.name}", values=values, error=error), (400 if error else 200)


@admin.route("/<int:recipe_id>/delete", methods=["GET", "POST"])
@admin_required
def confirm_delete(recipe_id):
    recipe = get_recipe_or_404(recipe_id)
    if request.method == "POST":
        name = recipe.name
        delete_recipe(recipe)
        flash(f"Deleted {name}.")
        return redirect(url_for("admin.recipe_list"))
    return render_template("admin_recipe_delete.html", recipe=recipe)

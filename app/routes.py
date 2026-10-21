from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.recipes import get_all_recipes, get_recipe
from app.servings import MAX_SERVINGS, MIN_SERVINGS, format_quantity, parse_servings, scale_ingredients

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/health")
def health():
    return {"status": "ok"}


@main.route("/recipes")
def recipes():
    return render_template("recipes.html", recipes=get_all_recipes())


@main.route("/recipes/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)
    return render_template("recipe_detail.html", recipe=recipe, format_quantity=format_quantity)


@main.route("/recipes/<int:recipe_id>/cook")
def cook(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)

    total_steps = len(recipe["steps"])
    step = request.args.get("step", default=1, type=int)
    servings, servings_error = parse_servings(request.args.get("servings"), recipe["base_servings"])

    # Keep the step in range so a bad or old link still lands on a real step.
    if step < 1 or step > total_steps:
        clamped = min(max(step, 1), total_steps)
        return redirect(url_for("main.cook", recipe_id=recipe_id, step=clamped, servings=servings))

    ingredients = scale_ingredients(recipe["ingredients"], recipe["base_servings"], servings)

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
    ), (400 if servings_error else 200)


@main.route("/recipes/<int:recipe_id>/cook/complete")
def cook_complete(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)

    # Saving the completion to the user's history is handled by PBI-08.
    return render_template("cook_complete.html", recipe=recipe)

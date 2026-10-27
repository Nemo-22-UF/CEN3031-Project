"""Recipe lookups used by the recipe and guided cooking pages.

Recipes are read from the database (the models in app/models.py) and turned
into plain dicts, so the templates don't need to know about the models.

SAMPLE_RECIPES are loaded into an empty database on startup, so the app has
something to show before anyone runs the TheMealDB importer.
"""

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import CookingStep, Ingredient, Recipe, RecipeIngredient

SAMPLE_RECIPES = {
    1: {
        "id": 1,
        "title": "Simple Scrambled Eggs",
        "base_servings": 1,
        "ingredients": [
            {"quantity": 2, "unit": "", "name": "eggs"},
            {"quantity": 1, "unit": "tbsp", "name": "butter"},
            {"quantity": 1, "unit": "tbsp", "name": "milk"},
            {"quantity": None, "unit": "", "name": "Salt and pepper, to taste"},
        ],
        "steps": [
            "Crack the eggs into a bowl, add the milk, and whisk until no streaks of white remain.",
            "Melt the butter in a nonstick pan over medium-low heat.",
            "Pour in the eggs and let them sit for about 20 seconds without stirring.",
            "Gently push the eggs from the edges toward the center with a spatula, forming soft curds.",
            "Take the pan off the heat while the eggs still look slightly wet. They will finish cooking on their own.",
            "Season with salt and pepper and serve right away.",
        ],
    },
    2: {
        "id": 2,
        "title": "Garlic Butter Pasta",
        "base_servings": 2,
        "ingredients": [
            {"quantity": 200, "unit": "g", "name": "spaghetti"},
            {"quantity": 3, "unit": "tbsp", "name": "butter"},
            {"quantity": 3, "unit": "cloves", "name": "garlic, minced"},
            {"quantity": 2, "unit": "tbsp", "name": "grated parmesan"},
            {"quantity": None, "unit": "", "name": "Salt, to taste"},
        ],
        "steps": [
            "Bring a large pot of salted water to a boil and cook the spaghetti until tender.",
            "Save a small cup of pasta water, then drain the spaghetti.",
            "Melt the butter in a pan over medium-low heat and cook the garlic for about 1 minute, until it smells fragrant.",
            "Add the spaghetti and a splash of pasta water, and toss until coated.",
            "Top with parmesan and serve.",
        ],
    },
    3: {
        "id": 3,
        "title": "Avocado Toast",
        "base_servings": 1,
        "ingredients": [
            {"quantity": 1, "unit": "slice", "name": "bread"},
            {"quantity": 1, "unit": "", "name": "ripe avocado"},
            {"quantity": 1, "unit": "tsp", "name": "lemon juice"},
            {"quantity": None, "unit": "", "name": "Salt and chili flakes, to taste"},
        ],
        "steps": [
            "Toast the bread until golden.",
            "Mash the avocado in a bowl with the lemon juice and a pinch of salt.",
            "Spread the avocado on the toast.",
            "Sprinkle with chili flakes and serve.",
        ],
    },
}


def recipe_to_dict(recipe):
    """Turn a Recipe model into the dict shape the templates use."""
    return {
        "id": recipe.id,
        "title": recipe.name,
        "base_servings": recipe.base_servings,
        "ingredients": [
            {"quantity": item.quantity, "unit": item.unit, "name": item.ingredient.name}
            for item in recipe.ingredients
        ],
        "steps": [step.instruction for step in recipe.steps],
    }


def get_recipe(recipe_id):
    """Return the recipe with this id, or None if it doesn't exist."""
    recipe = db.session.get(Recipe, recipe_id)
    return recipe_to_dict(recipe) if recipe else None


def get_all_recipes():
    """Return every recipe, oldest first."""
    return [recipe_to_dict(recipe) for recipe in Recipe.query.order_by(Recipe.id).all()]


def seed_sample_recipes():
    """Save SAMPLE_RECIPES if the database has no recipes yet. Safe to call again."""
    if Recipe.query.first() is not None:
        return

    ingredients = {item.name: item for item in Ingredient.query.all()}
    for sample in SAMPLE_RECIPES.values():
        recipe = Recipe(id=sample["id"], name=sample["title"], base_servings=sample["base_servings"])
        for item in sample["ingredients"]:
            ingredient = ingredients.setdefault(item["name"], Ingredient(name=item["name"]))
            recipe.ingredients.append(RecipeIngredient(ingredient=ingredient, quantity=item["quantity"], unit=item["unit"]))
        for number, instruction in enumerate(sample["steps"], start=1):
            recipe.steps.append(CookingStep(step_number=number, instruction=instruction))
        db.session.add(recipe)

    try:
        db.session.commit()
    except IntegrityError:
        # A database made before "to taste" quantities were allowed can't hold
        # the samples. Start anyway; deleting instance/app.db fixes it.
        db.session.rollback()
        print("Could not load the sample recipes. Delete instance/app.db and restart to rebuild the database.")

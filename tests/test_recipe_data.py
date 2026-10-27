"""The recipe pages read from the database, not from hard-coded data."""

from app import db
from app.models import CookingStep, Ingredient, Recipe, RecipeIngredient
from app.recipes import get_all_recipes, get_recipe, seed_sample_recipes


def add_recipe(name="Test Pancakes"):
    """Save a recipe straight to the database, the way the importer would."""
    recipe = Recipe(name=name, base_servings=2)
    recipe.ingredients.append(RecipeIngredient(ingredient=Ingredient(name="flour"), quantity=1, unit="cup"))
    recipe.steps.append(CookingStep(step_number=1, instruction="Mix the batter."))
    recipe.steps.append(CookingStep(step_number=2, instruction="Cook on a hot pan."))
    db.session.add(recipe)
    db.session.commit()
    return recipe.id


def test_seeding_loads_the_sample_recipes_once(app):
    with app.app_context():
        seed_sample_recipes()
        seed_sample_recipes()
        assert Recipe.query.count() == 3
        assert get_recipe(1)["title"] == "Simple Scrambled Eggs"


def test_to_taste_ingredients_are_stored_without_a_quantity(app):
    with app.app_context():
        seed_sample_recipes()
        salt = get_recipe(1)["ingredients"][-1]
        assert salt == {"quantity": None, "unit": "", "name": "Salt and pepper, to taste"}


def test_get_recipe_returns_none_for_unknown_id(app):
    with app.app_context():
        assert get_recipe(999) is None
        assert get_all_recipes() == []


def test_pages_show_a_recipe_added_to_the_database(app, client):
    with app.app_context():
        recipe_id = add_recipe()

    assert "Test Pancakes" in client.get("/recipes").get_data(as_text=True)

    detail = client.get(f"/recipes/{recipe_id}").get_data(as_text=True)
    assert "1 cup flour" in detail
    assert "Cook on a hot pan." in detail

    cook = client.get(f"/recipes/{recipe_id}/cook?servings=4").get_data(as_text=True)
    assert "Mix the batter." in cook
    assert "<strong>2 cup</strong>" in cook

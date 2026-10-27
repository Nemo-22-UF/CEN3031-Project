"""Tests for the TheMealDB importer. These use made-up meals, never the internet."""

from app.importer import import_meals, parse_measure, split_steps
from app.models import Recipe


def make_meal(name="Test Toast", category="Breakfast", ingredients=None, instructions="Toast the bread.\nEat it."):
    """Build a fake meal shaped like TheMealDB's API response."""
    meal = {"idMeal": "1", "strMeal": name, "strCategory": category, "strInstructions": instructions}
    for i, (ingredient, measure) in enumerate(ingredients or [("Bread", "2 slices")], start=1):
        meal[f"strIngredient{i}"] = ingredient
        meal[f"strMeasure{i}"] = measure
    return meal


def test_parse_measure():
    assert parse_measure("1/4 cup") == (0.25, "cup")
    assert parse_measure("1 1/2 tbsp") == (1.5, "tbsp")
    assert parse_measure("½ tsp") == (0.5, "tsp")
    assert parse_measure("200g") == (200, "g")
    assert parse_measure("3") == (3, "")
    assert parse_measure("to taste") is None
    assert parse_measure("") is None


def test_split_steps_drops_labels_and_numbers():
    text = "STEP 1\r\n1. Boil water.\r\n\r\nStep 2: Add pasta."
    assert split_steps(text) == ["Boil water.", "Add pasta."]


def test_import_saves_recipe(app):
    with app.app_context():
        imported, skipped = import_meals([make_meal(category="Vegan")])

        assert imported == 1
        recipe = Recipe.query.one()
        assert recipe.name == "Test Toast"
        assert recipe.base_servings == 1
        assert [step.instruction for step in recipe.steps] == ["Toast the bread.", "Eat it."]
        assert recipe.ingredients[0].ingredient.name == "bread"
        assert recipe.ingredients[0].quantity == 2
        assert sorted(tag.name for tag in recipe.tags) == ["main", "vegan", "vegetarian"]


def test_import_skips_meals_that_dont_fit(app):
    meals = [
        make_meal(name="Salty", ingredients=[("Salt", "to taste")]),
        make_meal(name="Double", ingredients=[("Egg", "1"), ("egg", "2")]),
    ]
    with app.app_context():
        imported, skipped = import_meals(meals)

        assert imported == 0
        assert skipped["ingredient without a measurable amount"] == 1
        assert skipped["same ingredient listed twice"] == 1
        assert Recipe.query.count() == 0


def test_import_twice_does_not_duplicate(app):
    with app.app_context():
        import_meals([make_meal()])
        imported, skipped = import_meals([make_meal()])

        assert imported == 0
        assert skipped["already in the database"] == 1
        assert Recipe.query.count() == 1

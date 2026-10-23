"""Recipe lookups used by the recipe and guided cooking pages.

For now this returns hard-coded sample data so the pages can be built
before the database models (PBI-02a) and recipe import (PBI-03b) are done.
Once those land, only get_recipe() and get_all_recipes() need to change.
"""

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


def get_recipe(recipe_id):
    """Return the recipe with this id, or None if it doesn't exist."""
    return SAMPLE_RECIPES.get(recipe_id)


def get_all_recipes():
    """Return every recipe."""
    return list(SAMPLE_RECIPES.values())

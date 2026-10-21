"""Recipe lookups used by the guided cooking pages.

For now this returns hard-coded sample data so guided cooking can be built
before the database models (PBI-02a) and recipe import (PBI-03b) are done.
Once those land, only get_recipe() needs to change to query the models.
"""

SAMPLE_RECIPES = {
    1: {
        "id": 1,
        "title": "Simple Scrambled Eggs",
        "base_servings": 1,
        "ingredients": [
            "2 eggs",
            "1 tbsp butter",
            "1 tbsp milk",
            "Salt and pepper",
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
}


def get_recipe(recipe_id):
    """Return the recipe with this id, or None if it doesn't exist."""
    return SAMPLE_RECIPES.get(recipe_id)

    

def get_all_recipes():
    return list(SAMPLE_RECIPES.values())

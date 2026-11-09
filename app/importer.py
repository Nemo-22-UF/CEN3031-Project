"""Import recipes from TheMealDB into our database (PBI-03b).

Run it with:

    flask --app run import-recipes

It downloads every recipe using TheMealDB's free search endpoint (one request
per letter of the alphabet), keeps the ones that fit our models, and saves them.
Recipes that are already in the database are left alone, so it's safe to run
more than once.

Known gaps for now (see docs/recipe-source.md):
- TheMealDB doesn't say how many servings a recipe makes, so every recipe is
  saved with base_servings = 1 (one batch).
- Recipes with an unmeasured ingredient ("salt, to taste") or the same
  ingredient listed twice are skipped, because our models can't store them yet.
"""

import json
import re
import string
import time
import urllib.request
from collections import Counter
from fractions import Fraction

import click

from app import db
from app.models import CookingStep, Ingredient, Recipe, RecipeIngredient, Tag

SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php?f={}"
BASE_SERVINGS = 1

# TheMealDB categories that tell us the meal type or diet. Everything else
# (Beef, Chicken, Pasta, etc.) counts as a main.
MEAL_TYPES = {"Breakfast": "breakfast", "Dessert": "dessert", "Starter": "starter", "Side": "side"}
DIETS = {"Vegetarian": ["vegetarian"], "Vegan": ["vegan", "vegetarian"]}

# Some measures use fraction characters".
FRACTION_CHARS = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4", "⅛": "1/8"}

# A measure starts with a number like "1 1/2", "1/4", "200" or "0.5",
# and anything after it is the unit.
MEASURE_PATTERN = re.compile(r"^(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*(.*)$")

# Lines like "STEP 1" or "2." are just labels, and lines often start with
# "1. " or "Step 2: ". We number steps ourselves, so both get dropped.
STEP_LABEL_PATTERN = re.compile(r"^(step\s*)?\d+[.):]?$", re.IGNORECASE)
STEP_NUMBER_PATTERN = re.compile(r"^(step\s*)?\d+[.):]\s+", re.IGNORECASE)


class SkippedMeal(Exception):
    """Raised when a TheMealDB meal can't be stored in our models."""


def parse_measure(measure):
    """Split a measure like "1/4 cup" into (0.25, "cup").

    Returns None when there's no usable number, like "to taste" or "pinch".
    """
    for char, fraction in FRACTION_CHARS.items():
        measure = measure.replace(char, f" {fraction}")

    match = MEASURE_PATTERN.match(measure.strip())
    if match is None:
        return None

    number, unit = match.group(1), match.group(2).strip()
    try:
        quantity = float(sum(Fraction(part) for part in number.split()))
    except ZeroDivisionError:
        return None

    if quantity <= 0 or len(unit) > 20:
        return None
    return quantity, unit


def split_steps(instructions):
    """Split TheMealDB's instruction text into a list of steps, one per line."""
    steps = []
    for line in instructions.splitlines():
        line = line.strip()
        if not line or STEP_LABEL_PATTERN.match(line):
            continue
        steps.append(STEP_NUMBER_PATTERN.sub("", line))
    return steps


def meal_tags(category):
    """Return our tag names for a TheMealDB category: a meal type plus any diets."""
    return [MEAL_TYPES.get(category, "main")] + DIETS.get(category, [])


def convert_meal(meal):
    """Pull out the parts of a TheMealDB meal that we store.

    Returns (name, ingredients, steps, tags), where ingredients is a list of
    (name, quantity, unit). Raises SkippedMeal if the meal doesn't fit.
    """
    name = (meal.get("strMeal") or "").strip()
    if not name or len(name) > 100:
        raise SkippedMeal("missing or too-long name")

    # TheMealDB stores ingredients in 20 numbered slots, and most are empty.
    ingredients = []
    seen = set()
    for i in range(1, 21):
        ingredient = (meal.get(f"strIngredient{i}") or "").strip().lower()
        if not ingredient:
            continue
        if ingredient in seen:
            raise SkippedMeal("same ingredient listed twice")
        measure = parse_measure(meal.get(f"strMeasure{i}") or "")
        if measure is None:
            raise SkippedMeal("ingredient without a measurable amount")
        seen.add(ingredient)
        ingredients.append((ingredient, *measure))

    steps = split_steps(meal.get("strInstructions") or "")
    if not ingredients or not steps:
        raise SkippedMeal("no ingredients or no steps")

    return name, ingredients, steps, meal_tags(meal.get("strCategory") or "")


def get_or_create(model, name):
    """Find an Ingredient or Tag by name, or make a new one."""
    item = model.query.filter_by(name=name).first()
    if item is None:
        item = model(name=name)
        db.session.add(item)
    return item


def import_meals(meals):
    """Save every meal that fits and isn't already in the database.

    Returns (number imported, Counter of skip reasons). Nothing is saved
    unless the whole batch succeeds.
    """
    imported = 0
    skipped = Counter()

    for meal in meals:
        try:
            name, ingredients, steps, tags = convert_meal(meal)
        except SkippedMeal as reason:
            skipped[str(reason)] += 1
            continue

        if Recipe.query.filter_by(name=name).first() is not None:
            skipped["already in the database"] += 1
            continue

        recipe = Recipe(name=name, base_servings=BASE_SERVINGS)
        for ingredient, quantity, unit in ingredients:
            recipe.ingredients.append(RecipeIngredient(
                ingredient=get_or_create(Ingredient, ingredient), quantity=quantity, unit=unit))
        for number, instruction in enumerate(steps, start=1):
            recipe.steps.append(CookingStep(step_number=number, instruction=instruction))
        recipe.tags = [get_or_create(Tag, tag) for tag in tags]
        db.session.add(recipe)
        imported += 1

    db.session.commit()
    return imported, skipped


def fetch_all_meals():
    """Download every TheMealDB meal, one request per letter a-z."""
    meals = []
    for letter in string.ascii_lowercase:
        with urllib.request.urlopen(SEARCH_URL.format(letter), timeout=10) as response:
            meals.extend(json.load(response)["meals"] or [])
        time.sleep(0.5)  # be polite to the free API
    return meals


@click.command("import-recipes")
def import_recipes_command():
    """Download recipes from TheMealDB and save the ones that fit."""
    click.echo("Downloading recipes from TheMealDB...")
    meals = fetch_all_meals()
    imported, skipped = import_meals(meals)

    click.echo(f"Imported {imported} of {len(meals)} recipes.")
    for reason, count in skipped.most_common():
        click.echo(f"  Skipped {count}: {reason}")

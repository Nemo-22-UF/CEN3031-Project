import re
import unicodedata

from app import db
from app.importer import parse_measure
from app.models import CookingStep, Ingredient, Recipe, RecipeIngredient
from app.servings import MAX_SERVINGS, MIN_SERVINGS

MAX_TITLE_LENGTH = 100
MAX_INGREDIENTS = 30
MAX_INGREDIENT_LENGTH = 100
MAX_STEPS = 30
MAX_STEP_LENGTH = 500
KNOWN_UNITS = {
    "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon", "teaspoons",
    "g", "gram", "grams", "kg", "ml", "l", "liter", "liters", "oz", "ounce", "ounces",
    "lb", "lbs", "pound", "pounds", "clove", "cloves", "slice", "slices", "can", "cans",
    "pinch", "pinches", "piece", "pieces", "stick", "sticks", "bunch", "handful",
}
LEADING_NUMBER = re.compile(r"^(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?|[½⅓⅔¼¾⅛])\s*")


class RecipeFormError(ValueError):
    pass


def clean_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = "".join(char for char in text if char in "\n\t" or unicodedata.category(char)[0] != "C")
    return re.sub(r"[ \t]+", " ", text).strip()


def non_empty_lines(text):
    return [line for line in (clean_text(raw) for raw in text.splitlines()) if line]


def parse_ingredient(line):
    match = LEADING_NUMBER.match(line)
    if match is None:
        return line, None, ""
    rest = line[match.end():]
    words = rest.split(" ", 1)
    if len(words) == 2 and words[0].lower().rstrip(".") in KNOWN_UNITS:
        measure, name = f"{match.group(1)} {words[0]}", words[1]
    else:
        measure, name = match.group(1), rest
    parsed = parse_measure(measure)
    if parsed is None or not name:
        return line, None, ""
    quantity, unit = parsed
    return name, quantity, unit


def parse_recipe_form(form):
    title = clean_text(form.get("title", ""))
    if len(title) < 3 or len(title) > MAX_TITLE_LENGTH:
        raise RecipeFormError(f"The title needs 3 to {MAX_TITLE_LENGTH} characters.")

    try:
        servings = int(form.get("servings", ""))
    except ValueError:
        servings = 0
    if not MIN_SERVINGS <= servings <= MAX_SERVINGS:
        raise RecipeFormError(f"Servings must be a whole number from {MIN_SERVINGS} to {MAX_SERVINGS}.")

    ingredient_lines = non_empty_lines(form.get("ingredients", ""))
    if not ingredient_lines:
        raise RecipeFormError("Add at least one ingredient.")
    if len(ingredient_lines) > MAX_INGREDIENTS:
        raise RecipeFormError(f"Recipes can have at most {MAX_INGREDIENTS} ingredients.")
    ingredients = [parse_ingredient(line) for line in ingredient_lines]
    for name, _, _ in ingredients:
        if len(name) > MAX_INGREDIENT_LENGTH:
            raise RecipeFormError(f"Each ingredient can be at most {MAX_INGREDIENT_LENGTH} characters.")
    names = [name.lower() for name, _, _ in ingredients]
    if len(names) != len(set(names)):
        raise RecipeFormError("Each ingredient can only be listed once.")

    steps = non_empty_lines(form.get("steps", ""))
    if not steps:
        raise RecipeFormError("Add at least one step.")
    if len(steps) > MAX_STEPS:
        raise RecipeFormError(f"Recipes can have at most {MAX_STEPS} steps.")
    if any(len(step) > MAX_STEP_LENGTH for step in steps):
        raise RecipeFormError(f"Each step can be at most {MAX_STEP_LENGTH} characters.")

    if Recipe.query.filter(db.func.lower(Recipe.name) == title.lower()).first():
        raise RecipeFormError("A recipe with that title already exists. Try another title.")

    return title, servings, ingredients, steps


def create_recipe(author, title, servings, ingredients, steps):
    recipe = Recipe(name=title, base_servings=servings, author_id=author.id)
    for name, quantity, unit in ingredients:
        ingredient = Ingredient.query.filter(db.func.lower(Ingredient.name) == name.lower()).first()
        recipe.ingredients.append(RecipeIngredient(
            ingredient=ingredient or Ingredient(name=name), quantity=quantity, unit=unit))
    for number, instruction in enumerate(steps, start=1):
        recipe.steps.append(CookingStep(step_number=number, instruction=instruction))
    db.session.add(recipe)
    db.session.commit()
    return recipe


def recipes_by(user_id):
    return Recipe.query.filter_by(author_id=user_id).order_by(Recipe.id.desc()).all()

import pytest
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Recipe, Ingredient, RecipeIngredient, Tag, CookingStep


def test_invalid_servings(app):
    with app.app_context():
        db.session.add(Recipe(name="Soup", base_servings=0))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_recipe(app):
    with app.app_context():
        recipe = Recipe(name="Pancakes", base_servings=2)
        ingredient = Ingredient(name="Flour")
        tag = Tag(name="Breakfast")
        recipe.ingredients.append(
            RecipeIngredient(ingredient=ingredient, quantity=1, unit="cup")
        )
        recipe.steps.append(CookingStep(step_number=1, instruction="Mix ingredients"))
        recipe.steps.append(CookingStep(step_number=2, instruction="Cook pancakes"))
        recipe.tags.append(tag)
        db.session.add(recipe)
        db.session.commit()
        saved = Recipe.query.filter_by(name="Pancakes").first()
        assert saved is not None
        assert saved.base_servings == 2
        assert saved.ingredients[0].quantity == 1
        assert saved.ingredients[0].unit == "cup"
        assert saved.ingredients[0].ingredient.name == "Flour"
        assert saved.tags[0].name == "Breakfast"
        assert [step.step_number for step in saved.steps] == [1, 2]


def test_duplicate_steps(app):
    with app.app_context():
        recipe = Recipe(name="Cake", base_servings=4)
        recipe.steps.append(CookingStep(step_number=1, instruction="Mix"))
        recipe.steps.append(CookingStep(step_number=1, instruction="Bake"))
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_invalid_relationship(app):
    with app.app_context():
        db.session.add(CookingStep(recipe_id=9999, step_number=1, instruction="Mix"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

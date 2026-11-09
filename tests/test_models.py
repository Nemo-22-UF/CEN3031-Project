
from app import create_app, db
from app.models import Recipe, Ingredient, RecipeIngredient, Tag, CookingStep
import pytest
from sqlalchemy.exc import IntegrityError


class TestingConfiguration:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

def test_invalid_servings():
    app = create_app(TestingConfiguration)
    with app.app_context():
        recipe = Recipe(name="Invalid", base_servings=0)
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_recipe():
    app = create_app(TestingConfiguration)
    with app.app_context():
        recipe = Recipe(name="Pancakes", base_servings=2)
        recipe.ingredients.append(
            RecipeIngredient(
                ingredient=Ingredient(name="Flour"),
                quantity=1,
                unit="cup"
            )
        )
        recipe.tags.append(Tag(name="Breakfast"))
        recipe.steps.append(CookingStep(step_number=2, instruction="Cook"))
        recipe.steps.append(CookingStep(step_number=1, instruction="Mix"))
        db.session.add(recipe)
        db.session.commit()
        recipe_id = recipe.id
        db.session.expire_all()
        saved = db.session.get(Recipe, recipe_id)
        assert saved.ingredients[0].quantity == 1
        assert saved.tags[0].name == "Breakfast"
        assert [s.step_number for s in saved.steps] == [1, 2]

def test_duplicate_steps():
    app = create_app(TestingConfiguration)

    with app.app_context():
        recipe = Recipe(name="Soup", base_servings=2)
        recipe.steps = [
            CookingStep(step_number=1, instruction="Boil"),
            CookingStep(step_number=1, instruction="Stir")
        ]

        db.session.add(recipe)

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
def test_invalid_relationship():
    app = create_app(TestingConfiguration)
    with app.app_context():
        item = RecipeIngredient(
            recipe_id=9999,
            ingredient_id=9999,
            quantity=1,
            unit="cup"
        )
        db.session.add(item)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

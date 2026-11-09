from app import db
from app.models import CookingStep, Ingredient, Recipe, RecipeIngredient


def add_one_step_recipe(app):
    with app.app_context():
        recipe = Recipe(name="Plain Toast", base_servings=1)
        recipe.steps.append(CookingStep(step_number=1, instruction="Toast the bread."))
        recipe.ingredients.append(
            RecipeIngredient(ingredient=Ingredient(name="test bread"), quantity=1, unit="slice")
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe.id


def test_detail_uses_singular_for_one(app, client):
    recipe_id = add_one_step_recipe(app)
    html = client.get(f"/recipes/{recipe_id}").get_data(as_text=True)
    assert ">1 step<" in html
    assert ">1 ingredient<" in html


def test_list_uses_singular_and_plural(app, client):
    add_one_step_recipe(app)
    html = client.get("/recipes").get_data(as_text=True)
    assert ">1 step<" in html
    assert ">1 steps<" not in html
    assert ">6 steps<" in html


def test_complete_page_with_one_step(app, client):
    recipe_id = add_one_step_recipe(app)
    html = client.get(f"/recipes/{recipe_id}/cook/complete").get_data(as_text=True)
    assert "the only step" in html

"""Admin recipe tools (PBI-17 and PBI-18)."""

import pytest

from app import db
from app.admin import parse_ingredient
from app.models import Completion, Favorite, Recipe, User


def log_in(app, client, username="chef", is_admin=True):
    with app.app_context():
        user = User(username=username, is_admin=is_admin)
        user.set_password("secret123")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    client.post("/login", data={"username": username, "password": "secret123"})
    return user_id


def recipe_form(**changes):
    form = {
        "title": "Pancakes",
        "servings": "2",
        "ingredients": "1 cup flour\n2 eggs\nSalt, to taste",
        "steps": "Mix everything.\nCook on a hot pan.",
    }
    form.update(changes)
    return form


def test_members_and_guests_cannot_use_admin_tools(app, client):
    assert client.get("/admin/recipes/").status_code == 302
    log_in(app, client, username="member", is_admin=False)
    assert client.get("/admin/recipes/").status_code == 403
    assert client.post("/admin/recipes/new", data=recipe_form()).status_code == 403
    assert client.post("/admin/recipes/1/delete").status_code == 403
    with app.app_context():
        assert db.session.get(Recipe, 1) is not None


def test_parse_ingredient():
    assert parse_ingredient("1 1/2 cups flour") == {"quantity": 1.5, "unit": "cups", "name": "flour"}
    assert parse_ingredient("2 eggs") == {"quantity": 2, "unit": "", "name": "eggs"}
    assert parse_ingredient("Salt, to taste") == {"quantity": None, "unit": "", "name": "Salt, to taste"}


def test_admin_adds_a_recipe(app, client):
    log_in(app, client)
    response = client.post("/admin/recipes/new", data=recipe_form())
    assert response.headers["Location"].endswith("/admin/recipes/")

    html = client.get("/recipes").get_data(as_text=True)
    assert "Pancakes" in html
    with app.app_context():
        recipe = Recipe.query.filter_by(name="Pancakes").one()
        assert [step.instruction for step in recipe.steps] == ["Mix everything.", "Cook on a hot pan."]
        assert len(recipe.ingredients) == 3


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"title": "ab"}, "3 to 100 characters"),
        ({"title": "simple scrambled eggs"}, "already exists"),
        ({"servings": "0"}, "Servings must be"),
        ({"steps": ""}, "Add 1 to 30 steps"),
        ({"ingredients": "2 eggs\n3 eggs"}, "only be listed once"),
    ],
)
def test_invalid_recipe_shows_error_and_saves_nothing(app, client, changes, message):
    log_in(app, client)
    response = client.post("/admin/recipes/new", data=recipe_form(**changes))
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    with app.app_context():
        assert Recipe.query.count() == 3


def test_admin_edits_a_recipe(app, client):
    log_in(app, client)
    form = client.get("/admin/recipes/3/edit").get_data(as_text=True)
    assert "Avocado Toast" in form

    client.post("/admin/recipes/3/edit", data=recipe_form(title="Better Avocado Toast", servings="4"))
    with app.app_context():
        recipe = db.session.get(Recipe, 3)
        assert recipe.name == "Better Avocado Toast"
        assert recipe.base_servings == 4
        assert len(recipe.steps) == 2


def test_delete_asks_first_then_removes_recipe_and_its_favorites(app, client):
    user_id = log_in(app, client)
    client.post("/recipes/1/favorite")
    with app.app_context():
        db.session.add(Completion(user_id=user_id, recipe_id=1, submission_token="abc"))
        db.session.commit()

    confirm = client.get("/admin/recipes/1/delete").get_data(as_text=True)
    assert "Delete Simple Scrambled Eggs?" in confirm
    with app.app_context():
        assert db.session.get(Recipe, 1) is not None

    client.post("/admin/recipes/1/delete")
    with app.app_context():
        assert db.session.get(Recipe, 1) is None
        assert Favorite.query.count() == 0
        assert Completion.query.count() == 0
    assert client.get("/recipes/1").status_code == 404

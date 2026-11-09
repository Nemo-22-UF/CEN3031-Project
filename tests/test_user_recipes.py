import pytest

from app import db
from app.models import Recipe, User
from app.user_recipes import parse_ingredient

GOOD = {
    "title": "Mom's Arepas",
    "servings": "4",
    "ingredients": "2 cups corn flour\n2 1/2 cups warm water\n1 tsp salt\nButter, to taste",
    "steps": "Mix the flour, water and salt.\n\nShape into discs.\nCook 5 minutes per side.",
}


def login(app, client, username="cook"):
    with app.app_context():
        user = User(username=username)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
    client.post("/login", data={"username": username, "password": "password"})


@pytest.mark.parametrize("line, expected", [
    ("2 cups flour", ("flour", 2.0, "cups")),
    ("1/2 tsp salt", ("salt", 0.5, "tsp")),
    ("2 1/2 cups water", ("water", 2.5, "cups")),
    ("3 eggs", ("eggs", 3.0, "")),
    ("½ cup milk", ("milk", 0.5, "cup")),
    ("Salt, to taste", ("Salt, to taste", None, "")),
])
def test_parse_ingredient(line, expected):
    assert parse_ingredient(line) == expected


def test_add_recipe_needs_login(client):
    assert "/login" in client.get("/recipes/new").headers["Location"]


def test_share_recipe(app, client):
    login(app, client)
    response = client.post("/recipes/new", data=GOOD)
    assert response.status_code == 302
    with app.app_context():
        recipe = Recipe.query.filter_by(name="Mom's Arepas").one()
        assert recipe.author.username == "cook"
        assert recipe.base_servings == 4
        assert [s.instruction for s in recipe.steps] == [
            "Mix the flour, water and salt.", "Shape into discs.", "Cook 5 minutes per side."]
        recipe_id = recipe.id
    html = client.get(f"/recipes/{recipe_id}").get_data(as_text=True)
    assert "Shared by" in html
    assert "2 1/2 cups warm water" in html


def test_shared_recipe_on_profile(app, client):
    login(app, client)
    client.post("/recipes/new", data=GOOD)
    client.post("/logout")
    html = client.get("/cooks/cook").get_data(as_text=True)
    assert "Mom&#39;s Arepas" in html
    assert "<strong>1</strong> recipe shared" in html


def test_script_is_shown_as_text(app, client):
    login(app, client)
    data = dict(GOOD, title="<script>alert(1)</script>", steps="<img src=x onerror=alert(1)>")
    client.post("/recipes/new", data=data)
    with app.app_context():
        recipe_id = Recipe.query.filter_by(name="<script>alert(1)</script>").one().id
    html = client.get(f"/recipes/{recipe_id}").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize("change, message", [
    ({"title": "ab"}, "3 to 100 characters"),
    ({"title": "x" * 101}, "3 to 100 characters"),
    ({"servings": "0"}, "Servings must be"),
    ({"servings": "lots"}, "Servings must be"),
    ({"ingredients": ""}, "at least one ingredient"),
    ({"ingredients": "\n".join(f"{i} g item{i}" for i in range(1, 32))}, "at most 30 ingredients"),
    ({"ingredients": "1 egg\n2 eggs\n1 Egg"}, "only be listed once"),
    ({"ingredients": "1 " + "a" * 101}, "at most 100 characters"),
    ({"steps": ""}, "at least one step"),
    ({"steps": "\n".join(["Stir."] * 31)}, "at most 30 steps"),
    ({"steps": "a" * 501}, "at most 500 characters"),
])
def test_rejects_bad_input(app, client, change, message):
    login(app, client)
    response = client.post("/recipes/new", data=dict(GOOD, **change))
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    with app.app_context():
        assert Recipe.query.filter_by(author_id=1).count() == 0


def test_rejects_duplicate_title(app, client):
    login(app, client)
    response = client.post("/recipes/new", data=dict(GOOD, title="simple scrambled eggs"))
    assert response.status_code == 400
    assert "already exists" in response.get_data(as_text=True)


def test_form_keeps_input_after_error(app, client):
    login(app, client)
    html = client.post("/recipes/new", data=dict(GOOD, servings="0")).get_data(as_text=True)
    assert "Mom&#39;s Arepas" in html
    assert "Shape into discs." in html


def test_control_characters_removed(app, client):
    login(app, client)
    client.post("/recipes/new", data=dict(GOOD, title="Tacos\x00\x07 de\u200b pollo"))
    with app.app_context():
        assert Recipe.query.filter_by(author_id=1).one().name == "Tacos de pollo"

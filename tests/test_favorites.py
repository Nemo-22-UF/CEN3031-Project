from app import db
from app.models import Favorite, User


def login(app, client, username="cook"):
    with app.app_context():
        user = User(username=username)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    client.post("/login", data={"username": username, "password": "password"})
    return user_id


def test_favorites_need_login(client):
    response = client.get("/favorites")
    assert "/login" in response.headers["Location"]


def test_add_favorite(app, client):
    login(app, client)
    client.post("/recipes/1/favorite")
    html = client.get("/favorites").get_data(as_text=True)
    assert "Simple Scrambled Eggs" in html
    assert "Garlic Butter Pasta" not in html


def test_remove_favorite(app, client):
    user_id = login(app, client)
    client.post("/recipes/1/favorite")
    client.post("/recipes/1/favorite")
    with app.app_context():
        assert Favorite.query.filter_by(user_id=user_id).count() == 0


def test_only_my_favorites(app, client):
    login(app, client, "cook1")
    client.post("/recipes/1/favorite")
    client.post("/logout")
    login(app, client, "cook2")
    html = client.get("/favorites").get_data(as_text=True)
    assert "Simple Scrambled Eggs" not in html


def test_favorite_button(app, client):
    login(app, client)
    assert "Add to favorites" in client.get("/recipes/1").get_data(as_text=True)
    client.post("/recipes/1/favorite")
    assert "Favorited" in client.get("/recipes/1").get_data(as_text=True)


def test_browse_hides_star_for_guests(client):
    assert "card-favorite" not in client.get("/recipes").get_data(as_text=True)


def test_favorite_from_browse(app, client):
    user_id = login(app, client)
    html = client.get("/recipes").get_data(as_text=True)
    assert "Add Simple Scrambled Eggs to favorites" in html
    response = client.post("/recipes/1/favorite", data={"next": "/recipes?q=eggs"})
    assert response.headers["Location"].endswith("/recipes?q=eggs")
    with app.app_context():
        assert Favorite.query.filter_by(user_id=user_id, recipe_id=1).count() == 1
    assert "Remove Simple Scrambled Eggs from favorites" in client.get("/recipes").get_data(as_text=True)


def test_favorite_ignores_outside_redirect(app, client):
    login(app, client)
    response = client.post("/recipes/1/favorite", data={"next": "//evil.example.com"})
    assert response.headers["Location"].endswith("/recipes/1")

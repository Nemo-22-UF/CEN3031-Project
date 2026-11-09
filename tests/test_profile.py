from app import db
from app.models import Completion, Favorite, User


def login(app, client, username="cook"):
    with app.app_context():
        user = User(username=username)
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    client.post("/login", data={"username": username, "password": "password"})
    return user_id


def test_profile_shows_defaults(app, client):
    login(app, client)
    html = client.get("/profile").get_data(as_text=True)
    assert "<h1>cook" in html
    assert "🍳" in html
    assert "No bio yet" in html
    assert "Edit profile" in html


def test_edit_bio_and_avatar(app, client):
    user_id = login(app, client)
    response = client.post("/profile/edit", data={"bio": "I love pasta", "avatar": "pasta"})
    assert response.headers["Location"].endswith("/profile")
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.bio == "I love pasta"
        assert user.avatar == "pasta"
    html = client.get("/profile").get_data(as_text=True)
    assert "I love pasta" in html
    assert "🍝" in html


def test_bio_too_long(app, client):
    login(app, client)
    response = client.post("/profile/edit", data={"bio": "a" * 161, "avatar": "egg"})
    assert response.status_code == 400
    assert "at most 160 characters" in response.get_data(as_text=True)


def test_unknown_avatar_rejected(app, client):
    login(app, client)
    response = client.post("/profile/edit", data={"bio": "", "avatar": "hacker"})
    assert response.status_code == 400


def test_bio_is_escaped(app, client):
    login(app, client)
    client.post("/profile/edit", data={"bio": "<script>alert(1)</script>", "avatar": "egg"})
    html = client.get("/profile").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_pick_top_favorites(app, client):
    user_id = login(app, client)
    for recipe_id in (1, 2, 3):
        client.post(f"/recipes/{recipe_id}/favorite")
    client.post("/profile/edit", data={"bio": "", "avatar": "egg", "top1": "3", "top2": "1", "top3": ""})
    with app.app_context():
        ranks = {f.recipe_id: f.rank for f in Favorite.query.filter_by(user_id=user_id)}
    assert ranks == {1: 2, 2: None, 3: 1}
    html = client.get("/profile").get_data(as_text=True)
    assert html.index("Avocado Toast") < html.index("Simple Scrambled Eggs")


def test_top_must_be_favorites(app, client):
    login(app, client)
    client.post("/recipes/1/favorite")
    response = client.post("/profile/edit", data={"avatar": "egg", "top1": "2"})
    assert response.status_code == 400


def test_top_must_be_different(app, client):
    login(app, client)
    client.post("/recipes/1/favorite")
    response = client.post("/profile/edit", data={"avatar": "egg", "top1": "1", "top2": "1"})
    assert response.status_code == 400


def test_stats_count_completions(app, client):
    user_id = login(app, client)
    with app.app_context():
        db.session.add_all([
            Completion(user_id=user_id, recipe_id=1, submission_token="a"),
            Completion(user_id=user_id, recipe_id=1, submission_token="b"),
            Completion(user_id=user_id, recipe_id=2, submission_token="c"),
        ])
        db.session.commit()
    html = client.get("/profile").get_data(as_text=True)
    assert "<strong>3</strong> times cooked" in html
    assert "<strong>2</strong> different recipes" in html


def test_public_profile(app, client):
    login(app, client, "maria")
    client.post("/profile/edit", data={"bio": "Hi", "avatar": "taco"})
    client.post("/logout")
    html = client.get("/cooks/Maria").get_data(as_text=True)
    assert "<h1>maria" in html
    assert "Hi" in html
    assert "Edit profile" not in html
    assert client.get("/cooks/nobody").status_code == 404


def test_edit_needs_login(client):
    assert "/login" in client.get("/profile/edit").headers["Location"]

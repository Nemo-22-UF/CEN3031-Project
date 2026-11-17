from app import db
from app.models import RecipeProgress, User
from tests.conftest import app

def login(app, client, username= "testuser", password= "password"):
   with app.app_context():
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )

def test_progress_status_display(app, client):
    login(app, client)
    client.get("/recipes/1/cook?step=1")
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Started</span>' in html
    client.get("/recipes/1/cook?step=6")
    client.get("/recipes/1/cook/complete")
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Finished</span>' in html

def  test_guest_user_progress_not_displayed(app, client):
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Started</span>' not in html

def test_progress_status_persists_across_sessions(app, client):
    login(app, client)
    client.get("/recipes/1/cook?step=1")
    client.post("/logout")
    login(app, client)
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Started</span>' in html

def test_progress_status_for_multiple_recipes(app, client):
    login(app, client)
    client.get("/recipes/1/cook?step=1")
    client.get("/recipes/2/cook?step=1")
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Started</span>' in html
    with app.app_context():
        progress= RecipeProgress.query.all()
        assert len(progress) == 2
        assert {recipe.recipe_id for recipe in progress} == {1, 2}

def test_progress_status_updates_correctly(app, client):
    login(app, client)
    client.get("/recipes/1/cook?step=1")
    client.get("/recipes/1/cook?step=2")
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Started</span>' in html
    with app.app_context():
     progress = RecipeProgress.query.filter_by(recipe_id=1).one()
     assert progress.current_step == 2
     assert progress.status == "started"
    client.get("/recipes/1/cook?step=6")
    client.get("/recipes/1/cook/complete")
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Finished</span>' in html
    with app.app_context():
        progress = RecipeProgress.query.filter_by(recipe_id=1).one()
        assert progress.status == "finished"

def test_separate_progress_for_different_users(app, client):
    login(app, client, username="user1", password="password1")
    client.get("/recipes/1/cook?step=1")
    client.post("/logout")
    login(app, client, username="user2", password="password2")
    client.get("/recipes/1/cook?step=3")
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert '<span class="badge">Status: Started</span>' in html
    with app.app_context():
        user1 = User.query.filter_by(username="user1").first()
        user2 = User.query.filter_by(username="user2").first()
        progress_user1 = RecipeProgress.query.filter_by(user_id=user1.id, recipe_id=1).one()
        progress_user2 = RecipeProgress.query.filter_by(user_id=user2.id, recipe_id=1).one()
        assert progress_user1.current_step == 1
        assert progress_user2.current_step == 3
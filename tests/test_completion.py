from app import db
from app.models import User, Completion

def test_save_completion(app, client):
    with app.app_context():
        user = User(username="cook")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client.post("/login", data={
        "username": "cook",
        "password": "password"
    })
    url = "/recipes/1/cook/save"
    data = {"token": "test-session-123"}
    response = client.post(url, data=data)
    assert response.status_code == 302
    response = client.post(url, data=data)
    assert response.status_code == 302
    with app.app_context():
        saved = Completion.query.filter_by(user_id=user_id).all()
        assert len(saved) == 1
        assert saved[0].recipe_id == 1
        assert saved[0].completed_at is not None

def test_login_required(client):
    response = client.post(
        "/recipes/1/cook/save",
        data={"token": "another-session"}
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
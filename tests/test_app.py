from sqlalchemy import text

from app import db


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_database_connection(app):
    with app.app_context():
        assert db.session.execute(text("SELECT 1")).scalar() == 1


from app import create_app, db
from app.models import User, Recipe, Favorite, Completion
import pytest
from sqlalchemy.exc import IntegrityError

def test_user_persistence():
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        user1 = User(username="user1")
        user1.set_password("password123")

        user2 = User(username="user2")
        user2.set_password("password456")

        recipe = Recipe(name="Pancakes", base_servings=2)

        db.session.add_all([user1, user2, recipe])
        db.session.flush()

        db.session.add_all([
            Favorite(user_id=user1.id, recipe_id=recipe.id),
            Completion(user_id=user1.id, recipe_id=recipe.id)
        ])
        db.session.commit()

        db.session.expire_all()

        assert Favorite.query.filter_by(user_id=user1.id).count() == 1
        assert Completion.query.filter_by(user_id=user1.id).count() == 1
        assert Favorite.query.filter_by(user_id=user2.id).count() == 0
        assert Completion.query.filter_by(user_id=user2.id).count() == 0


def test_persistence(app):
    with app.app_context():
        user1 = User(username="user1")
        user1.set_password("password1")

        user2 = User(username="user2")
        user2.set_password("password2")

        recipe = Recipe(name="Pancakes", base_servings=2)

        db.session.add_all([user1, user2, recipe])
        db.session.flush()

        db.session.add_all([
            Favorite(user_id=user1.id, recipe_id=recipe.id),
            Completion(user_id=user1.id, recipe_id=recipe.id)
        ])
        db.session.commit()
        db.session.expire_all()

        assert Favorite.query.filter_by(user_id=user1.id).count() == 1
        assert Completion.query.filter_by(user_id=user1.id).count() == 1
        assert Favorite.query.filter_by(user_id=user2.id).count() == 0
        assert Completion.query.filter_by(user_id=user2.id).count() == 0


def test_duplicate_favorite(app):
    with app.app_context():
        user = User(username="user")
        user.set_password("password")
        recipe = Recipe(name="Soup", base_servings=2)

        db.session.add_all([user, recipe])
        db.session.flush()

        db.session.add_all([
            Favorite(user_id=user.id, recipe_id=recipe.id),
            Favorite(user_id=user.id, recipe_id=recipe.id)
        ])

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

import pytest
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Recipe, Favorite, Completion

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
            Completion(
                user_id=user1.id,
                recipe_id=recipe.id,
                submission_token="test-token-1"
            )
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

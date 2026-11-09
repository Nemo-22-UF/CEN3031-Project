
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone
from app import db

recipe_tags = db.Table(
    "recipe_tags",
    db.Column("recipe_id", db.Integer, db.ForeignKey("recipe.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    bio = db.Column(db.String(160), nullable=False, default="")
    avatar = db.Column(db.String(20), nullable=False, default="egg")
    joined_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_servings = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    author = db.relationship("User", backref="recipes")
    __table_args__ = (db.CheckConstraint("base_servings > 0"),)
    ingredients = db.relationship("RecipeIngredient", backref="recipe", cascade="all, delete-orphan")
    steps = db.relationship("CookingStep", backref="recipe", order_by="CookingStep.step_number", cascade="all, delete-orphan")
    tags = db.relationship("Tag", secondary=recipe_tags, backref="recipes")

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class RecipeIngredient(db.Model):
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), primary_key=True)
    quantity = db.Column(db.Float, nullable=True)  # None for "to taste" items
    unit = db.Column(db.String(20), nullable=False)
    ingredient = db.relationship("Ingredient")
    __table_args__ = (db.CheckConstraint("quantity > 0"),)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class CookingStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    instruction = db.Column(db.Text, nullable=False)
    __table_args__ = (
        db.CheckConstraint("step_number > 0"),
        db.UniqueConstraint("recipe_id", "step_number")
    )

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    rank = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "recipe_id"),
        db.CheckConstraint("rank BETWEEN 1 AND 3"),
    )


class Completion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    completed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    submission_token = db.Column(db.String(64), unique=True, nullable=False)


def get_favorites(user_id):
    return Favorite.query.filter_by(user_id=user_id).all()

def get_completions(user_id):
    return Completion.query.filter_by(user_id=user_id).all()
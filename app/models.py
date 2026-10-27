
from app import db

recipe_tags = db.Table(
    "recipe_tags",
    db.Column("recipe_id", db.Integer, db.ForeignKey("recipe.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    base_servings = db.Column(db.Integer, nullable=False)
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

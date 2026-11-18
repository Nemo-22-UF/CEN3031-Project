from app import db
from app.models import Completion, Favorite
from app.recipes import get_recipe

AVATARS = {
    "egg": "🍳",
    "avocado": "🥑",
    "pasta": "🍝",
    "cake": "🍰",
    "pizza": "🍕",
    "taco": "🌮",
    "croissant": "🥐",
    "sushi": "🍣",
}
MAX_BIO_LENGTH = 160
TOP_FAVORITES = 3


def avatar_emoji(user):
    return AVATARS.get(user.avatar, AVATARS["egg"])


def favorite_recipes(user_id):
    favorites = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.id).all()
    recipes = [(favorite, get_recipe(favorite.recipe_id)) for favorite in favorites]
    return [(favorite, recipe) for favorite, recipe in recipes if recipe]


def top_favorites(user_id):
    ranked = [pair for pair in favorite_recipes(user_id) if pair[0].rank]
    return [recipe for favorite, recipe in sorted(ranked, key=lambda pair: pair[0].rank)]


def profile_stats(user_id):
    completions = Completion.query.filter_by(user_id=user_id).all()
    return {
        "cooked": len(completions),
        "unique_recipes": len({completion.recipe_id for completion in completions}),
        "favorites": Favorite.query.filter_by(user_id=user_id).count(),
    }


def profile_error(bio, avatar, top_ids, favorite_ids):
    if len(bio) > MAX_BIO_LENGTH:
        return f"Your bio can be at most {MAX_BIO_LENGTH} characters."
    if avatar not in AVATARS:
        return "Pick one of the avatars."
    chosen = [recipe_id for recipe_id in top_ids if recipe_id is not None]
    if len(chosen) != len(set(chosen)):
        return "Pick a different recipe for each top spot."
    if any(recipe_id not in favorite_ids for recipe_id in chosen):
        return "Your top recipes have to be in your favorites."
    return None


def save_profile(user, bio, avatar, top_ids):
    user.bio = bio
    user.avatar = avatar
    favorites = {favorite.recipe_id: favorite for favorite in Favorite.query.filter_by(user_id=user.id)}
    for favorite in favorites.values():
        favorite.rank = None
    db.session.flush()
    for rank, recipe_id in enumerate(top_ids, start=1):
        if recipe_id is not None:
            favorites[recipe_id].rank = rank
    db.session.commit()

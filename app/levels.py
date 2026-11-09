from datetime import datetime, timedelta, timezone

from app.models import Completion

XP_PER_COOK = 10
XP_NEW_RECIPE = 15
TITLES = ["Kitchen Newbie", "Home Cook", "Line Cook", "Sous Chef", "Head Chef", "Master Chef"]


def xp_for_level(level):
    return 25 * (level - 1) * level


def level_for_xp(xp):
    level = 1
    while xp >= xp_for_level(level + 1):
        level += 1
    return level


def title_for_level(level):
    return TITLES[min(level, len(TITLES)) - 1]


def total_xp(completions):
    return XP_PER_COOK * len(completions) + XP_NEW_RECIPE * len({c.recipe_id for c in completions})


def cooking_streak(completions, today=None):
    today = today or datetime.now(timezone.utc).date()
    days = {c.completed_at.date() for c in completions}
    day = today if today in days else today - timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def level_info(user_id):
    completions = Completion.query.filter_by(user_id=user_id).all()
    xp = total_xp(completions)
    level = level_for_xp(xp)
    start, end = xp_for_level(level), xp_for_level(level + 1)
    return {
        "xp": xp,
        "level": level,
        "title": title_for_level(level),
        "next_xp": end,
        "xp_to_next": end - xp,
        "progress": round(100 * (xp - start) / (end - start)),
        "streak": cooking_streak(completions),
    }

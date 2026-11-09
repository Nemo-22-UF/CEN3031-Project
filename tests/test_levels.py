from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from app import db
from app.levels import cooking_streak, level_for_xp, title_for_level, total_xp, xp_for_level
from app.models import Completion, User


def done(recipe_id, day=date(2026, 11, 9)):
    return SimpleNamespace(recipe_id=recipe_id, completed_at=datetime(day.year, day.month, day.day, 12))


def login(app, client):
    with app.app_context():
        user = User(username="cook")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    client.post("/login", data={"username": "cook", "password": "password"})
    return user_id


def test_level_thresholds():
    assert [xp_for_level(n) for n in range(1, 5)] == [0, 50, 150, 300]
    assert level_for_xp(0) == 1
    assert level_for_xp(49) == 1
    assert level_for_xp(50) == 2
    assert level_for_xp(299) == 3


def test_titles_cap_at_master_chef():
    assert title_for_level(1) == "Kitchen Newbie"
    assert title_for_level(99) == "Master Chef"


def test_new_recipes_earn_bonus():
    assert total_xp([done(1)]) == 25
    assert total_xp([done(1), done(1)]) == 35
    assert total_xp([done(1), done(2)]) == 50


def test_streak():
    today = date(2026, 11, 9)
    days = [today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=4)]
    assert cooking_streak([done(1, d) for d in days], today) == 3
    assert cooking_streak([done(1, today - timedelta(days=1))], today) == 1
    assert cooking_streak([done(1, today - timedelta(days=2))], today) == 0
    assert cooking_streak([], today) == 0


def test_profile_shows_level(app, client):
    login(app, client)
    html = client.get("/profile").get_data(as_text=True)
    assert "Level 1" in html
    assert "Kitchen Newbie" in html
    assert "50 XP to level 2" in html


def test_finishing_a_recipe_awards_xp_and_levels_up(app, client):
    user_id = login(app, client)
    response = client.post("/recipes/1/cook/save", data={"token": "one"}, follow_redirects=True)
    assert "+25 XP" in response.get_data(as_text=True)
    response = client.post("/recipes/2/cook/save", data={"token": "two"}, follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "+25 XP" in html
    assert "Level up! You&#39;re now level 2: Home Cook." in html
    html = client.get("/profile").get_data(as_text=True)
    assert "Level 2" in html
    assert "🔥 1 day" in html


def test_resubmitting_gives_no_extra_xp(app, client):
    login(app, client)
    client.post("/recipes/1/cook/save", data={"token": "same"})
    client.get("/recipes")
    response = client.post("/recipes/1/cook/save", data={"token": "same"}, follow_redirects=True)
    assert 'class="flash">+' not in response.get_data(as_text=True)

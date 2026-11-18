from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app import db
from app.levels import cooking_streak, level_for_xp, local_day, title_for_level, total_xp, xp_for_level
from app.models import User


def done(recipe_id, when=datetime(2026, 11, 18, 17, 0)):
    return SimpleNamespace(recipe_id=recipe_id, completed_at=when)


def login(app, client):
    with app.app_context():
        user = User(username="cook")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
    client.post("/login", data={"username": "cook", "password": "password"})


def test_level_thresholds():
    assert [xp_for_level(n) for n in range(1, 7)] == [0, 50, 150, 300, 500, 750]
    assert [level_for_xp(x) for x in (0, 49, 50, 299, 300)] == [1, 1, 2, 3, 4]


def test_titles():
    assert title_for_level(1) == "Newbie"
    assert title_for_level(99) == "Master Chef"


def test_new_recipe_bonus():
    assert total_xp([done(1)]) == 25
    assert total_xp([done(1), done(1)]) == 35
    assert total_xp([done(1), done(2)]) == 50


def test_streak_counts_days_in_a_row():
    today = date(2026, 11, 18)
    days = [0, 1, 2, 4]
    completions = [done(1, datetime(2026, 11, 18 - d, 17, 0)) for d in days]
    assert cooking_streak(completions, today) == 3


def test_streak_still_active_from_yesterday():
    assert cooking_streak([done(1, datetime(2026, 11, 17, 17, 0))], date(2026, 11, 18)) == 1


def test_streak_broken():
    assert cooking_streak([done(1, datetime(2026, 11, 15, 17, 0))], date(2026, 11, 18)) == 0


def test_streak_uses_eastern_time():
    late_night_utc = datetime(2026, 11, 19, 2, 0)
    assert local_day(late_night_utc) == date(2026, 11, 18)


def test_finishing_gives_xp_once(app, client):
    login(app, client)
    first = client.post("/recipes/1/cook/save", data={"token": "a"}, follow_redirects=True)
    assert "+25 XP" in first.get_data(as_text=True)
    again = client.post("/recipes/1/cook/save", data={"token": "a"}, follow_redirects=True)
    assert "XP</p>" not in again.get_data(as_text=True)


def test_level_up_message(app, client):
    login(app, client)
    client.post("/recipes/1/cook/save", data={"token": "a"})
    html = client.post("/recipes/2/cook/save", data={"token": "b"}, follow_redirects=True).get_data(as_text=True)
    assert "Level up!" in html


def test_profile_shows_level(app, client):
    login(app, client)
    html = client.get("/profile").get_data(as_text=True)
    assert "Level 1" in html
    assert "50 XP to level 2" in html

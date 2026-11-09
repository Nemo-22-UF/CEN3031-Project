from fractions import Fraction

import pytest

from app.servings import format_quantity, format_unit, parse_servings, scale_ingredients


INGREDIENTS = [
    {"quantity": 2, "unit": "", "name": "eggs"},
    {"quantity": 0.5, "unit": "cup", "name": "milk"},
    {"quantity": None, "unit": "", "name": "Salt, to taste"},
]


def test_scale_ingredients_multiplies_quantities():
    scaled = scale_ingredients(INGREDIENTS, base_servings=1, servings=3)
    assert scaled[0]["quantity"] == 6
    assert scaled[1]["quantity"] == Fraction(3, 2)


def test_scale_ingredients_can_scale_down():
    scaled = scale_ingredients(INGREDIENTS, base_servings=4, servings=1)
    assert scaled[0]["quantity"] == Fraction(1, 2)
    assert scaled[1]["quantity"] == Fraction(1, 8)


def test_scale_ingredients_leaves_unmeasured_items_alone():
    scaled = scale_ingredients(INGREDIENTS, base_servings=1, servings=5)
    assert scaled[2]["quantity"] is None
    assert scaled[2]["name"] == "Salt, to taste"


def test_scale_ingredients_does_not_change_the_original():
    scale_ingredients(INGREDIENTS, base_servings=1, servings=10)
    assert INGREDIENTS[0]["quantity"] == 2


@pytest.mark.parametrize(
    "quantity, expected",
    [(3, "3"), (Fraction(1, 2), "1/2"), (Fraction(3, 2), "1 1/2"), (0.25, "1/4"), (None, "")],
)
def test_format_quantity(quantity, expected):
    assert format_quantity(quantity) == expected


@pytest.mark.parametrize("raw, expected", [(None, 2), ("", 2), ("1", 1), ("20", 20), ("7", 7)])
def test_parse_servings_accepts_valid_values(raw, expected):
    assert parse_servings(raw, default=2) == (expected, None)


@pytest.mark.parametrize("raw", ["0", "21", "25", "-3", "abc", "2.5"])
def test_parse_servings_rejects_invalid_values(raw):
    servings, error = parse_servings(raw, default=2)
    assert servings == 2
    assert error is not None


def test_cook_page_scales_ingredients(client):
    html = client.get("/recipes/1/cook?servings=3").get_data(as_text=True)
    assert "Ingredients for 3 servings" in html
    assert "<strong>6</strong>" in html
    assert "<strong>3 tbsp</strong>" in html


def test_cook_page_defaults_to_base_servings(client):
    html = client.get("/recipes/1/cook").get_data(as_text=True)
    assert "Ingredients for 1 serving" in html
    assert "<strong>2</strong>" in html


@pytest.mark.parametrize("bad", ["0", "25", "abc"])
def test_cook_page_rejects_invalid_servings(client, bad):
    response = client.get(f"/recipes/1/cook?servings={bad}")
    html = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Servings must be" in html
    assert "Ingredients for 1 serving" in html


def test_step_links_keep_the_chosen_servings(client):
    html = client.get("/recipes/1/cook?step=2&servings=4").get_data(as_text=True)
    assert "/recipes/1/cook?step=1&amp;servings=4" in html
    assert "/recipes/1/cook?step=3&amp;servings=4" in html


@pytest.mark.parametrize(
    "unit, quantity, expected",
    [
        ("slice", 2, "slices"),
        ("slice", 1, "slice"),
        ("cloves", 1, "clove"),
        ("cloves", Fraction(3, 2), "cloves"),
        ("cup", Fraction(1, 2), "cup"),
        ("leaf", 4, "leaves"),
        ("tbsp", 3, "tbsp"),
        ("g", 200, "g"),
        ("", 2, ""),
    ],
)
def test_format_unit_matches_the_amount(unit, quantity, expected):
    assert format_unit(unit, quantity) == expected


def test_cook_page_pluralizes_scaled_units(client):
    # Avocado toast is recipe 3 and uses 1 slice of bread for 1 serving.
    html = client.get("/recipes/3/cook?servings=2").get_data(as_text=True)
    assert "<strong>2 slices</strong>" in html
    assert "2 slice<" not in html


def test_cook_page_keeps_singular_for_one(client):
    html = client.get("/recipes/3/cook?servings=1").get_data(as_text=True)
    assert "<strong>1 slice</strong>" in html

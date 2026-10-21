import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_cook_page_starts_on_first_step(client):
    response = client.get("/recipes/1/cook")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Step 1 of 6" in html
    assert "Crack the eggs into a bowl" in html
    assert "Next step" in html


def test_cook_page_shows_requested_step(client):
    response = client.get("/recipes/1/cook?step=3")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Step 3 of 6" in html
    assert "let them sit for about 20 seconds" in html
    assert "/recipes/1/cook?step=2" in html
    assert "/recipes/1/cook?step=4" in html


def test_last_step_links_to_finish(client):
    response = client.get("/recipes/1/cook?step=6")
    html = response.get_data(as_text=True)
    assert "Step 6 of 6" in html
    assert "Finish cooking" in html
    assert "/recipes/1/cook/complete" in html
    assert "Next step" not in html


def test_out_of_range_step_redirects_to_valid_step(client):
    too_high = client.get("/recipes/1/cook?step=99")
    assert too_high.status_code == 302
    assert too_high.headers["Location"].endswith("/recipes/1/cook?step=6")

    too_low = client.get("/recipes/1/cook?step=0")
    assert too_low.status_code == 302
    assert too_low.headers["Location"].endswith("/recipes/1/cook?step=1")


def test_completion_page(client):
    response = client.get("/recipes/1/cook/complete")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "You made Simple Scrambled Eggs!" in html


def test_unknown_recipe_returns_404(client):
    assert client.get("/recipes/999/cook").status_code == 404
    assert client.get("/recipes/999/cook/complete").status_code == 404

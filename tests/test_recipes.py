def test_home_links_to_recipes(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "/recipes" in html

def test_recipes_page_lists_recipes(client):
    response = client.get("/recipes")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Simple Scrambled Eggs" in html
    assert "/recipes/1" in html

def test_recipe_detail_shows_ingredients_and_steps(client):
    response = client.get("/recipes/1")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Simple Scrambled Eggs" in html
    assert "2 eggs" in html
    assert "Crack the eggs into a bowl" in html
    assert "/recipes/1/cook?step=1" in html

def test_unknown_recipe_detail_returns_404(client):
    assert client.get("/recipes/999").status_code == 404
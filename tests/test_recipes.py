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

def test_recipes_page_shows_every_recipe(client):
    html = client.get("/recipes").get_data(as_text=True)
    assert "Simple Scrambled Eggs" in html
    assert "Garlic Butter Pasta" in html
    assert "Avocado Toast" in html
    
def test_home_explains_how_it_works(client):
    html = client.get("/").get_data(as_text=True)
    assert "How Skill-It works" in html
    assert "Start cooking" in html
    assert 'button-large" href="/register">Sign up</a>' in html
    assert 'button-large" href="/login">Log in</a>' in html

def test_search_finds_matching_recipe(client):
    html = client.get("/recipes?q=pasta").get_data(as_text=True)
    assert "Garlic Butter Pasta" in html
    assert "Avocado Toast" not in html

def test_search_ignores_case(client):
    html = client.get("/recipes?q=EGGS").get_data(as_text=True)
    assert "Simple Scrambled Eggs" in html

def test_search_with_no_match_links_to_all_recipes(client):
    html = client.get("/recipes?q=sushi").get_data(as_text=True)
    assert "Your search has no matches" in html
    assert "full recipe list" in html

def test_empty_search_shows_every_recipe(client):
    html = client.get("/recipes?q=").get_data(as_text=True)
    assert "Simple Scrambled Eggs" in html
    assert "Garlic Butter Pasta" in html
    assert "Avocado Toast" in html

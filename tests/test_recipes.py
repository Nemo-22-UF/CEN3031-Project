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
def test_nav_highlights_current_page(client):
    html = client.get("/recipes").get_data(as_text=True)
    assert 'nav-link active" href="/recipes"' in html

def test_include_needs_every_ingredient(client):
    html = client.get("/recipes?include=eggs&include=butter").get_data(as_text=True)
    assert "Simple Scrambled Eggs" in html
    assert "Garlic Butter Pasta" not in html

def test_exclude_removes_recipes_with_that_ingredient(client):
    html = client.get("/recipes?exclude=butter").get_data(as_text=True)
    assert "Avocado Toast" in html
    assert "Simple Scrambled Eggs" not in html
    assert "Garlic Butter Pasta" not in html

def test_diet_filter(client):
    html = client.get("/recipes?diet=vegan").get_data(as_text=True)
    assert "Avocado Toast" in html
    assert "Simple Scrambled Eggs" not in html

def test_meal_type_filter(client):
    html = client.get("/recipes?meal=breakfast").get_data(as_text=True)
    assert "Simple Scrambled Eggs" in html
    assert "Avocado Toast" in html
    assert "Garlic Butter Pasta" not in html

def test_filters_combine(client):
    html = client.get("/recipes?include=salt&exclude=milk&meal=breakfast&diet=vegetarian").get_data(as_text=True)
    assert "Avocado Toast" in html
    assert "Simple Scrambled Eggs" not in html
    assert "Garlic Butter Pasta" not in html

def test_filters_with_no_match_show_message(client):
    html = client.get("/recipes?diet=vegan&meal=dessert").get_data(as_text=True)
    assert "Your search has no matches" in html

def test_ingredient_match_keeps_real_ingredients(client):
    assert client.get("/ingredients/match?name=butter").get_json() == {"name": "butter"}

def test_ingredient_match_fixes_spelling(client):
    assert client.get("/ingredients/match?name=garlicss").get_json() == {"name": "garlic"}

def test_ingredient_match_rejects_unknown_ingredients(client):
    assert client.get("/ingredients/match?name=xyzzy").get_json() == {"name": None}

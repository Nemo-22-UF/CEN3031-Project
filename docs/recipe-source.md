# Recipe Source Decision (PBI-03a)

## Decision
Use TheMealDB (free test API, key "1") as our recipe source and import its full
dataset (~790 recipes) so search and filters have plenty to work with.
Start with a small hand-validated sample of ~20–30 recipes, then import the rest.

## TheMealDB
- API docs: https://www.themealdb.com/api.php
- Terms: the test key "1" may be used during development or for educational use.
- Example: https://www.themealdb.com/api/json/v1/1/search.php?s=Arrabiata

## Usage rules
The free key does not include the "list every recipe" endpoint; that is a paid
supporter feature. We can still collect every recipe with free endpoints
(see "How to get recipes from the API"), but we keep our use light and fair:

- **Import once, read locally.** The import script downloads the recipes into our
  database. The app reads from our database, not from TheMealDB, while people use it.
- **Re-run the import only when needed** (e.g. after resetting the database), and
  pause about 0.5 seconds between requests.
- **Don't commit downloaded data to the repo.** Each developer runs the import script
  to fill their own database.
- **Credit TheMealDB** in the app and in the README.
- **Educational use only.** If the app is ever released publicly, we must become a
  TheMealDB supporter, as their terms require.
- **Check the full terms of use** linked from the API page before the full import,
  and email thedatadb@gmail.com if anything is unclear.

## Survey of the full dataset (790 recipes, 38 cuisines)
- 87% of ingredients have a numeric measure ("1/4 cup"); 13% do not ("pinch", "to taste").
- 175 recipes list the same ingredient twice.
- 768 recipes have line-separated instructions that split cleanly into steps.
- 232 recipes fit our models with no changes.
- About 25 measures contain broken characters (e.g. "� tsp").

## Field mapping
| Our model field                 | TheMealDB field                 | Notes |
|---------------------------------|---------------------------------|-------|
| Recipe.name                     | strMeal                         | Max 100 chars |
| Recipe.base_servings            | (none)                          | Set by hand for the sample; use a default (e.g. 4) for the full import |
| Ingredient.name                 | strIngredient1–20               | Skip empty; lowercase to avoid duplicates |
| RecipeIngredient.quantity, unit | strMeasure1–20                  | Split "1/4 cup" into 0.25 + "cup" |
| CookingStep.step_number, instruction | strInstructions            | Split on line breaks; number in order |
| Tag.name (meal type)            | strCategory                     | Breakfast/Dessert/Starter/Side map directly |
| Tag.name (diet)                 | strCategory                     | Vegetarian, Vegan; others added by hand |

## Import plan
1. **Sample (~20–30 recipes):** pick recipes with only numeric measures, no duplicate
   ingredients, and line-separated instructions, covering breakfast, mains, sides,
   desserts and at least 3 vegetarian/vegan recipes. Set base servings by hand.
2. **Full dataset (~790 recipes):** import everything else once the sample works.
   This needs decisions on the data that does not fit our models today:
   - "to taste" / "pinch" ingredients (13%): `RecipeIngredient.quantity` cannot be
     empty, so either allow empty quantities or skip those ingredients.
   - Duplicate ingredients in one recipe (175 recipes): merge or skip the repeat.
   - No serving counts: use a default `base_servings` value.
   - Broken characters in measures: fix or skip.

## How to get recipes from the API
These free endpoints cover what we need:

| Endpoint | Returns |
|----------|---------|
| `search.php?f=<letter>` | Every recipe whose name starts with that letter, with full details |
| `filter.php?c=<category>` | Name and ID of every recipe in a category (no details) |
| `lookup.php?i=<id>` | One recipe in full, by ID |
| `random.php` | One random recipe in full |

All URLs start with `https://www.themealdb.com/api/json/v1/1/`.

- **Full import:** call `search.php?f=a` through `search.php?f=z` (26 requests) and
  combine the results. This is how the 790-recipe survey above was produced.
- **Browsing for the sample:** use `filter.php?c=Breakfast` (or Dessert, Side,
  Starter, Vegetarian, Vegan, Beef, Chicken, ...) to see candidate names and IDs.
- **Importing the sample:** call `lookup.php?i=<id>` once per chosen recipe.

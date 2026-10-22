"""Serving-size scaling for recipe ingredients."""

from fractions import Fraction

MIN_SERVINGS = 1
MAX_SERVINGS = 20


def parse_servings(raw, default):
    """Turn a servings value from the URL into an int.

    Returns (servings, error). If raw is missing, servings is the default.
    If raw is not a whole number from MIN_SERVINGS to MAX_SERVINGS, servings
    falls back to the default and error explains why.
    """
    if raw is None or raw == "":
        return default, None

    try:
        servings = int(raw)
    except (TypeError, ValueError):
        return default, f"Servings must be a whole number from {MIN_SERVINGS} to {MAX_SERVINGS}."

    if servings < MIN_SERVINGS or servings > MAX_SERVINGS:
        return default, f"Servings must be from {MIN_SERVINGS} to {MAX_SERVINGS}."

    return servings, None


def scale_ingredients(ingredients, base_servings, servings):
    """Return a copy of the ingredients with quantities scaled to servings.

    Ingredients without a quantity (like "salt to taste") are left as-is.
    """
    factor = Fraction(servings, base_servings)
    scaled = []
    for ingredient in ingredients:
        item = dict(ingredient)
        if item.get("quantity") is not None:
            item["quantity"] = Fraction(str(item["quantity"])) * factor
        scaled.append(item)
    return scaled


def format_quantity(quantity):
    """Format a quantity for display, using fractions instead of decimals.

    Examples: 3 -> "3", 0.5 -> "1/2", 1.5 -> "1 1/2".
    """
    if quantity is None:
        return ""

    quantity = Fraction(quantity).limit_denominator(8)
    whole, remainder = divmod(quantity.numerator, quantity.denominator)

    if remainder == 0:
        return str(whole)
    fraction = f"{remainder}/{quantity.denominator}"
    return f"{whole} {fraction}" if whole else fraction

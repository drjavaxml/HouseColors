"""Load and search paint brand color databases."""

import json
from pathlib import Path
from lib.color_utils import hex_to_rgb, color_distance

BRANDS_DIR = Path(__file__).resolve().parent.parent / "data" / "paint_brands"


def load_brand(filename: str) -> dict:
    """Load a single brand JSON file."""
    with open(BRANDS_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_brands() -> list[dict]:
    """Load every brand JSON in the paint_brands directory."""
    brands = []
    for path in sorted(BRANDS_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            brands.append(json.load(f))
    return brands


def search_by_name(query: str, brands: list[dict] | None = None) -> list[dict]:
    """Return colors whose name contains *query* (case-insensitive)."""
    if brands is None:
        brands = load_all_brands()
    query_lower = query.lower()
    results = []
    for brand in brands:
        for color in brand["colors"]:
            if query_lower in color["name"].lower():
                results.append({**color, "brand": brand["brand"]})
    return results


def find_closest(hex_str: str, n: int = 5, brands: list[dict] | None = None) -> list[dict]:
    """Return the *n* closest paint colors to the given hex value."""
    if brands is None:
        brands = load_all_brands()
    target = hex_to_rgb(hex_str)
    scored = []
    for brand in brands:
        for color in brand["colors"]:
            dist = color_distance(target, hex_to_rgb(color["hex"]))
            scored.append({**color, "brand": brand["brand"], "distance": round(dist, 2)})
    scored.sort(key=lambda c: c["distance"])
    return scored[:n]

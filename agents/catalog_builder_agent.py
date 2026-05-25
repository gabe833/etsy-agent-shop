import json
import re

from config import PRODUCT_CATALOG_PATH
from agents.printify_helper import printify_get


TARGET_PRODUCTS = {
    "t-shirt": {
        "keywords": ["bella", "canvas", "unisex", "jersey", "short sleeve", "t-shirt"],
        "exclude_keywords": ["kids", "youth", "baby", "infant", "long sleeve", "v-neck", "tank"],
        "default_price": 24.99,
        "print_position": "front",
        "preferred_colors": [
            "white",
            "natural",
            "ash",
            "heather dust",
            "athletic heather",
            "silver",
            "light grey",
            "light gray"
        ],
        "preferred_sizes": ["S", "M", "L", "XL"]
    },
    "sweatshirt": {
        "keywords": ["unisex", "crewneck", "sweatshirt"],
        "exclude_keywords": ["kids", "youth", "baby", "infant", "hoodie", "zip"],
        "default_price": 39.99,
        "print_position": "front",
        "preferred_colors": [
            "white",
            "sand",
            "ash",
            "sport grey",
            "light pink",
            "light blue"
        ],
        "preferred_sizes": ["S", "M", "L", "XL"]
    },
    "mug": {
        "keywords": ["mug", "11oz"],
        "exclude_keywords": ["travel", "tumbler", "bottle"],
        "default_price": 16.99,
        "print_position": "front",
        "preferred_colors": ["white"],
        "preferred_sizes": []
    },
    "tote": {
        "keywords": ["tote", "bag"],
        "exclude_keywords": ["backpack", "duffel", "lunch"],
        "default_price": 21.99,
        "print_position": "front",
        "preferred_colors": ["natural", "white", "canvas"],
        "preferred_sizes": []
    }
}


PREFERRED_PROVIDERS = [
    "SwiftPOD",
    "Monster Digital",
    "Awkward Styles",
    "Print Clever",
    "District Photo",
    "MWW",
    "Duplium",
    "Generic brand"
]


def normalize_text(text):
    return (text or "").lower().strip()


def score_blueprint(blueprint, product_rules):
    title = normalize_text(blueprint.get("title"))
    brand = normalize_text(blueprint.get("brand"))

    combined = f"{title} {brand}"

    score = 0

    for keyword in product_rules["keywords"]:
        if keyword.lower() in combined:
            score += 5

    for keyword in product_rules["exclude_keywords"]:
        if keyword.lower() in combined:
            score -= 20

    if "unisex" in combined:
        score += 5

    if "bella" in combined or "canvas" in combined:
        score += 8

    if "gildan" in combined:
        score += 5

    if "heavy blend" in combined:
        score += 4

    return score


def choose_best_blueprint(blueprints, product_rules):
    scored = []

    for blueprint in blueprints:
        score = score_blueprint(blueprint, product_rules)

        if score > 0:
            scored.append((score, blueprint))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def score_provider(provider):
    title = provider.get("title", "")

    for index, preferred in enumerate(PREFERRED_PROVIDERS):
        if preferred.lower() in title.lower():
            return 100 - index

    return 10


def choose_best_provider(providers):
    if not providers:
        return None

    scored = [(score_provider(provider), provider) for provider in providers]
    scored.sort(key=lambda item: item[0], reverse=True)

    return scored[0][1]


def option_text(variant):
    parts = []

    title = variant.get("title")
    if title:
        parts.append(str(title))

    options = variant.get("options") or {}
    if isinstance(options, dict):
        for value in options.values():
            parts.append(str(value))

    return " ".join(parts).lower()


def variant_matches_color(variant, preferred_colors):
    text = option_text(variant)

    if not preferred_colors:
        return True

    return any(color.lower() in text for color in preferred_colors)


def variant_matches_size(variant, preferred_sizes):
    text = option_text(variant)

    if not preferred_sizes:
        return True

    tokens = re.split(r"[^a-zA-Z0-9]+", text.upper())

    return any(size.upper() in tokens for size in preferred_sizes)


def choose_variants(variants, product_rules, max_variants=8):
    chosen = []

    for variant in variants:
        if variant.get("is_enabled") is False:
            continue

        if not variant_matches_color(variant, product_rules["preferred_colors"]):
            continue

        if not variant_matches_size(variant, product_rules["preferred_sizes"]):
            continue

        variant_id = variant.get("id")

        if variant_id:
            chosen.append(variant_id)

        if len(chosen) >= max_variants:
            break

    if not chosen:
        for variant in variants:
            if variant.get("is_enabled") is False:
                continue

            variant_id = variant.get("id")

            if variant_id:
                chosen.append(variant_id)

            if len(chosen) >= max_variants:
                break

    return chosen


def build_catalog():
    print("Fetching Printify blueprints...")

    blueprints = printify_get("/catalog/blueprints.json")

    catalog = {}

    for product_type, rules in TARGET_PRODUCTS.items():
        print(f"\nBuilding catalog entry for: {product_type}")

        blueprint = choose_best_blueprint(blueprints, rules)

        if not blueprint:
            print(f"No blueprint found for {product_type}. Skipping.")
            continue

        blueprint_id = blueprint.get("id")
        blueprint_title = blueprint.get("title")
        blueprint_brand = blueprint.get("brand")

        print(f"Selected blueprint: {blueprint_id} | {blueprint_title} | {blueprint_brand}")

        try:
            providers = printify_get(f"/catalog/blueprints/{blueprint_id}/print_providers.json")
        except Exception as e:
            print(f"Could not fetch providers for {product_type}: {e}")
            continue

        provider = choose_best_provider(providers)

        if not provider:
            print(f"No provider found for {product_type}. Skipping.")
            continue

        provider_id = provider.get("id")
        provider_title = provider.get("title")

        print(f"Selected provider: {provider_id} | {provider_title}")

        try:
            variant_data = printify_get(
                f"/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json"
            )
        except Exception as e:
            print(f"Could not fetch variants for {product_type}: {e}")
            continue

        variants = variant_data.get("variants", [])
        variant_ids = choose_variants(variants, rules)

        if not variant_ids:
            print(f"No variants found for {product_type}. Skipping.")
            continue

        print(f"Selected variants: {variant_ids}")

        catalog[product_type] = {
            "display_name": blueprint_title,
            "blueprint_id": blueprint_id,
            "blueprint_brand": blueprint_brand,
            "print_provider_id": provider_id,
            "print_provider_title": provider_title,
            "variant_ids": variant_ids,
            "default_price": rules["default_price"],
            "print_position": rules["print_position"],
            "allowed_design_colors": ["black"],
            "selection_method": "auto_catalog_builder",
            "notes": "Auto-selected from Printify catalog using product rules."
        }

    with open(PRODUCT_CATALOG_PATH, "w") as file:
        json.dump(catalog, file, indent=2)

    print(f"\nProduct catalog saved to: {PRODUCT_CATALOG_PATH}")
    print(json.dumps(catalog, indent=2))


def run_catalog_builder_agent():
    build_catalog()


if __name__ == "__main__":
    run_catalog_builder_agent()
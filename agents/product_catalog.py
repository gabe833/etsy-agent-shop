import json
from pathlib import Path

from config import PRODUCT_CATALOG_PATH


def load_product_catalog():
    if not Path(PRODUCT_CATALOG_PATH).exists():
        raise FileNotFoundError(f"Product catalog not found: {PRODUCT_CATALOG_PATH}")

    with open(PRODUCT_CATALOG_PATH, "r") as file:
        return json.load(file)


def product_is_configured(product_type):
    catalog = load_product_catalog()

    if product_type not in catalog:
        return False

    settings = catalog[product_type]

    return (
        settings.get("blueprint_id", 0) != 0
        and settings.get("print_provider_id", 0) != 0
        and len(settings.get("variant_ids", [])) > 0
    )


def get_allowed_product_types():
    catalog = load_product_catalog()

    available = []

    for product_type in catalog:
        if product_is_configured(product_type):
            available.append(product_type)

    return available


def normalize_product_type(product_type):
    if not product_type:
        return "t-shirt"

    product_type = product_type.lower().strip()

    mapping = {
        "shirt": "t-shirt",
        "tee": "t-shirt",
        "tshirt": "t-shirt",
        "t-shirt": "t-shirt",
        "sweatshirt": "sweatshirt",
        "crewneck": "sweatshirt",
        "crewneck sweatshirt": "sweatshirt",
        "mug": "mug",
        "coffee mug": "mug",
        "tote": "tote",
        "tote bag": "tote",
        "bag": "tote"
    }

    return mapping.get(product_type, product_type)


def get_product_settings(product_type):
    catalog = load_product_catalog()
    normalized = normalize_product_type(product_type)

    if normalized not in catalog:
        raise ValueError(f"Product type '{product_type}' is not in product_catalog.json.")

    settings = catalog[normalized]

    if not product_is_configured(normalized):
        raise ValueError(
            f"Product type '{normalized}' is not fully configured. "
            f"Run: python main.py catalog"
        )

    return normalized, settings
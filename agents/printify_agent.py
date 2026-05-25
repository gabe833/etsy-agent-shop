import sqlite3
from pathlib import Path

from PIL import Image

from config import DB_PATH, PRINTIFY_SHOP_ID

from agents.product_catalog import get_product_settings
from agents.printify_helper import upload_image_to_printify, printify_post


def get_latest_design_ready_for_printify():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        designs.id,
        designs.product_idea_id,
        designs.design_file_path,
        designs.main_text,
        designs.design_width,
        designs.design_height,
        product_ideas.product_name,
        product_ideas.product_type,
        listing_drafts.title,
        listing_drafts.description,
        listing_drafts.tags,
        listing_drafts.suggested_price
    FROM designs
    LEFT JOIN product_ideas ON designs.product_idea_id = product_ideas.id
    LEFT JOIN listing_drafts ON listing_drafts.product_idea_id = product_ideas.id
    WHERE designs.status = 'review_passed'
    ORDER BY designs.id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "design_id": row[0],
        "product_idea_id": row[1],
        "design_file_path": row[2],
        "main_text": row[3],
        "design_width": row[4],
        "design_height": row[5],
        "product_name": row[6],
        "product_type": row[7],
        "title": row[8],
        "description": row[9],
        "tags": row[10],
        "suggested_price": row[11],
    }


def save_printify_product(product_idea_id, printify_product_id, title, design_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO printify_products (
        product_idea_id,
        printify_product_id,
        printify_shop_id,
        title,
        status
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        product_idea_id,
        printify_product_id,
        PRINTIFY_SHOP_ID,
        title,
        "created"
    ))

    cursor.execute("""
    UPDATE designs
    SET status = 'uploaded_to_printify'
    WHERE id = ?
    """, (design_id,))

    conn.commit()
    conn.close()


def cents(price):
    return int(float(price) * 100)


def get_design_size(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Design file not found: {file_path}")

    with Image.open(path) as img:
        return img.size


def calculate_printify_placement(product_type, design_width, design_height):
    aspect_ratio = design_width / design_height if design_height else 1

    if product_type == "mug":
        if aspect_ratio > 4:
            scale = 0.55
        elif aspect_ratio > 2:
            scale = 0.70
        else:
            scale = 0.82

        return {
            "x": 0.5,
            "y": 0.5,
            "scale": scale,
            "angle": 0
        }

    if product_type == "tote":
        if aspect_ratio > 3:
            scale = 0.48
        elif aspect_ratio > 2:
            scale = 0.56
        else:
            scale = 0.64

        return {
            "x": 0.5,
            "y": 0.36,
            "scale": scale,
            "angle": 0
        }

    if product_type == "sweatshirt":
        if aspect_ratio > 4:
            scale = 0.58
        elif aspect_ratio > 3:
            scale = 0.68
        elif aspect_ratio > 2:
            scale = 0.80
        else:
            scale = 0.92

        return {
            "x": 0.5,
            "y": 0.42,
            "scale": scale,
            "angle": 0
        }

    if aspect_ratio > 4:
        scale = 0.62
    elif aspect_ratio > 3:
        scale = 0.70
    elif aspect_ratio > 2:
        scale = 0.82
    else:
        scale = 0.95

    return {
        "x": 0.5,
        "y": 0.42,
        "scale": scale,
        "angle": 0
    }


def get_price(item, product_settings):
    if item.get("suggested_price"):
        return cents(item["suggested_price"])

    return cents(product_settings.get("default_price", 24.99))


def build_printify_product_payload(item, uploaded_image_id):
    product_type, product_settings = get_product_settings(item["product_type"])

    blueprint_id = product_settings["blueprint_id"]
    print_provider_id = product_settings["print_provider_id"]
    variant_ids = product_settings["variant_ids"]
    print_position = product_settings.get("print_position", "front")

    if not variant_ids:
        raise ValueError(f"No variant IDs configured for product type: {product_type}")

    price = get_price(item, product_settings)

    variants = []
    for variant_id in variant_ids:
        variants.append({
            "id": variant_id,
            "price": price,
            "is_enabled": True
        })

    design_width, design_height = get_design_size(item["design_file_path"])

    placement = calculate_printify_placement(
        product_type=product_type,
        design_width=design_width,
        design_height=design_height
    )

    print("\nProduct type selected:")
    print(product_type)

    print("\nProduct settings:")
    print(product_settings)

    print("\nCalculated Printify placement:")
    print(placement)

    payload = {
        "title": item["title"] or item["product_name"],
        "description": item["description"] or "",
        "blueprint_id": blueprint_id,
        "print_provider_id": print_provider_id,
        "variants": variants,
        "print_areas": [
            {
                "variant_ids": variant_ids,
                "placeholders": [
                    {
                        "position": print_position,
                        "images": [
                            {
                                "id": uploaded_image_id,
                                "x": placement["x"],
                                "y": placement["y"],
                                "scale": placement["scale"],
                                "angle": placement["angle"]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    return payload


def run_printify_agent():
    if not PRINTIFY_SHOP_ID:
        print("Missing PRINTIFY_SHOP_ID in .env.")
        return

    item = get_latest_design_ready_for_printify()

    if not item:
        print("No review-passed designs ready for Printify.")
        print("Run: python main.py design_review")
        return

    try:
        product_type, _ = get_product_settings(item["product_type"])
    except Exception as e:
        print(f"Product catalog error: {e}")
        return

    print(f"Uploading reviewed design to Printify: {item['design_file_path']}")
    print(f"Product type: {product_type}")

    uploaded = upload_image_to_printify(item["design_file_path"])
    uploaded_image_id = uploaded.get("id")

    if not uploaded_image_id:
        print("Upload failed. No image ID returned.")
        print(uploaded)
        return

    print(f"Uploaded image ID: {uploaded_image_id}")

    payload = build_printify_product_payload(item, uploaded_image_id)

    print("Creating Printify product...")

    created_product = printify_post(
        f"/shops/{PRINTIFY_SHOP_ID}/products.json",
        payload
    )

    printify_product_id = created_product.get("id")

    if not printify_product_id:
        print("Product creation failed. No product ID returned.")
        print(created_product)
        return

    save_printify_product(
        product_idea_id=item["product_idea_id"],
        printify_product_id=printify_product_id,
        title=created_product.get("title", item["title"]),
        design_id=item["design_id"]
    )

    print("\nPrintify product created successfully.")
    print(f"Printify Product ID: {printify_product_id}")
    print("Review it in Printify before publishing.")


if __name__ == "__main__":
    run_printify_agent()
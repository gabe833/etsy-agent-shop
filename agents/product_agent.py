import json
import sqlite3
from pathlib import Path

from agents.ollama_helper import ask_ollama
from agents.product_catalog import get_allowed_product_types, normalize_product_type


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def get_latest_new_niche():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, niche_name, target_buyer, notes
    FROM niches
    WHERE status = 'new'
    ORDER BY id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "niche_name": row[1],
        "target_buyer": row[2],
        "notes": row[3]
    }


def clean_json_response(response_text):
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    json_text = response_text[start:end + 1]
    return json.loads(json_text)


def save_product_idea(niche_id, product):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO product_ideas (
        niche_id,
        product_name,
        product_type,
        target_buyer,
        design_concept,
        suggested_price,
        risk_level,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        niche_id,
        product.get("product_name"),
        product.get("product_type"),
        product.get("target_buyer"),
        product.get("design_concept"),
        product.get("suggested_price"),
        product.get("risk_level"),
        "draft"
    ))

    cursor.execute("""
    UPDATE niches
    SET status = 'product_created'
    WHERE id = ?
    """, (niche_id,))

    conn.commit()
    conn.close()


def run_product_agent():
    niche = get_latest_new_niche()

    if not niche:
        print("No new niches found. Run the Research Agent first.")
        return

    allowed_product_types = get_allowed_product_types()

    if not allowed_product_types:
        print("No configured product types found in data/product_catalog.json.")
        print("Run: python main.py catalog")
        return

    allowed_text = ", ".join(allowed_product_types)

    prompt = f"""
You are the Product Development Agent for an Etsy print-on-demand shop.

Create ONE specific product idea from this niche.

Niche:
{niche["niche_name"]}

Target buyer:
{niche["target_buyer"]}

Notes:
{niche["notes"]}

Allowed product types:
{allowed_text}

Rules:
- Choose the product type that best fits the niche and design idea.
- Product type MUST be exactly one of the allowed product types.
- Avoid trademarked phrases, celebrities, characters, brands, sports teams, song lyrics, and copyrighted content.
- Keep the design simple enough for print-on-demand.
- Make the idea original, giftable, and actually sellable.
- Avoid vague concepts.
- Avoid random travel/location phrases unless the niche clearly supports travel.

Return ONLY valid JSON.
Do not include any explanation before or after the JSON.

Use this exact format:

{{
  "product_name": "Product name here",
  "product_type": "t-shirt",
  "target_buyer": "Target buyer here",
  "design_concept": "Describe the design concept here.",
  "suggested_price": 24.99,
  "risk_level": "low"
}}
"""

    print(f"Product Agent is creating a product for niche: {niche['niche_name']}")

    response = ask_ollama(prompt)

    if response.startswith("ERROR"):
        print(response)
        return

    print("\nRaw Ollama response:")
    print(response)

    try:
        product = clean_json_response(response)

        product_type = normalize_product_type(product.get("product_type"))

        if product_type not in allowed_product_types:
            print(f"Model chose unavailable product type: {product.get('product_type')}")
            print(f"Allowed product types: {allowed_text}")
            print("Defaulting to first available product type.")
            product_type = allowed_product_types[0]

        product["product_type"] = product_type

        save_product_idea(niche["id"], product)
        print(f"\nProduct idea saved to database as product type: {product_type}")

    except Exception as e:
        print("\nCould not save product idea.")
        print(f"Error: {e}")
        print("\nThe model may not have returned clean JSON. Try running it again.")


if __name__ == "__main__":
    run_product_agent()
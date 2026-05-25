import json
import sqlite3
from pathlib import Path

from agents.ollama_helper import ask_ollama


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def get_latest_draft_product():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, product_name, product_type, target_buyer, design_concept, suggested_price, risk_level
    FROM product_ideas
    WHERE status = 'draft'
    ORDER BY id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "product_name": row[1],
        "product_type": row[2],
        "target_buyer": row[3],
        "design_concept": row[4],
        "suggested_price": row[5],
        "risk_level": row[6]
    }


def clean_json_response(response_text):
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    json_text = response_text[start:end + 1]
    return json.loads(json_text)


def save_listing_draft(product_id, listing):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tags = listing.get("tags", [])

    if isinstance(tags, list):
        tags = ", ".join(tags)

    cursor.execute("""
    INSERT INTO listing_drafts (
        product_idea_id,
        title,
        description,
        tags,
        suggested_price,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        product_id,
        listing.get("title"),
        listing.get("description"),
        tags,
        listing.get("suggested_price"),
        "draft"
    ))

    cursor.execute("""
    UPDATE product_ideas
    SET status = 'listing_created'
    WHERE id = ?
    """, (product_id,))

    conn.commit()
    conn.close()


def run_listing_agent():
    product = get_latest_draft_product()

    if not product:
        print("No draft product ideas found. Run the Product Agent first.")
        return

    prompt = f"""
You are the Etsy Listing SEO Agent for a print-on-demand Etsy shop.

Create an Etsy listing draft for this product.

Product name:
{product["product_name"]}

Product type:
{product["product_type"]}

Target buyer:
{product["target_buyer"]}

Design concept:
{product["design_concept"]}

Suggested price:
{product["suggested_price"]}

Rules:
- Title must be under 140 characters.
- Title must clearly include what the item is, such as shirt, sweatshirt, mug, or tote.
- Do not use trademarked names, celebrities, Disney, Bluey, Barbie, Taylor Swift, NFL, NCAA, college names, song lyrics, movie quotes, or brand names.
- Do not use "inspired by" trademarked products.
- Make it sound natural and buyer-friendly.
- Tags should be realistic Etsy search phrases.
- Return exactly 13 tags.
- Description should clearly explain that this is a made-to-order print-on-demand item.
- Do not make guarantees.
- Do not mention fake materials or shipping times.
- Keep it professional but warm.

Return ONLY valid JSON.
Do not include any explanation before or after the JSON.

Use this exact format:

{{
  "title": "Etsy title here",
  "description": "Full Etsy description here",
  "tags": [
    "tag one",
    "tag two",
    "tag three",
    "tag four",
    "tag five",
    "tag six",
    "tag seven",
    "tag eight",
    "tag nine",
    "tag ten",
    "tag eleven",
    "tag twelve",
    "tag thirteen"
  ],
  "suggested_price": 24.99
}}
"""

    print(f"Listing Agent is creating a listing for: {product['product_name']}")

    response = ask_ollama(prompt)

    if response.startswith("ERROR"):
        print(response)
        return

    print("\nRaw Ollama response:")
    print(response)

    try:
        listing = clean_json_response(response)
        save_listing_draft(product["id"], listing)
        print("\nListing draft saved to database.")

    except Exception as e:
        print("\nCould not save listing draft.")
        print(f"Error: {e}")
        print("\nThe model may not have returned clean JSON. Try running it again.")


if __name__ == "__main__":
    run_listing_agent()
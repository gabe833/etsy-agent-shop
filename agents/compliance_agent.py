import json
import sqlite3
from pathlib import Path

from agents.ollama_helper import ask_ollama


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


BANNED_TERMS = [
    "disney",
    "bluey",
    "barbie",
    "taylor swift",
    "swiftie",
    "nfl",
    "nba",
    "mlb",
    "ncaa",
    "harry potter",
    "pokemon",
    "star wars",
    "marvel",
    "nike",
    "stanley",
    "lululemon"
]


def get_latest_listing_for_review():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        listing_drafts.id,
        listing_drafts.product_idea_id,
        product_ideas.product_name,
        product_ideas.product_type,
        product_ideas.design_concept,
        listing_drafts.title,
        listing_drafts.description,
        listing_drafts.tags,
        listing_drafts.suggested_price
    FROM listing_drafts
    LEFT JOIN product_ideas ON listing_drafts.product_idea_id = product_ideas.id
    WHERE listing_drafts.status = 'draft'
    ORDER BY listing_drafts.id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "listing_id": row[0],
        "product_idea_id": row[1],
        "product_name": row[2],
        "product_type": row[3],
        "design_concept": row[4],
        "title": row[5],
        "description": row[6],
        "tags": row[7],
        "suggested_price": row[8]
    }


def basic_banned_term_check(text):
    text_lower = text.lower()
    found = []

    for term in BANNED_TERMS:
        if term in text_lower:
            found.append(term)

    return found


def clean_json_response(response_text):
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    json_text = response_text[start:end + 1]
    return json.loads(json_text)


def save_compliance_result(listing, result):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO compliance_checks (
        product_idea_id,
        listing_draft_id,
        result,
        risk_level,
        issues_found,
        recommendation
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        listing["product_idea_id"],
        listing["listing_id"],
        result.get("result"),
        result.get("risk_level"),
        result.get("issues_found"),
        result.get("recommendation")
    ))

    if result.get("result") == "PASS":
        cursor.execute("""
        UPDATE listing_drafts
        SET status = 'compliance_passed'
        WHERE id = ?
        """, (listing["listing_id"],))

        cursor.execute("""
        INSERT INTO approval_queue (
            action_type,
            item_type,
            item_id,
            summary,
            risk_level,
            status,
            approved
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "create_printify_product",
            "listing_draft",
            listing["listing_id"],
            f"Ready to create Printify product for: {listing['product_name']}",
            result.get("risk_level"),
            "pending",
            0
        ))

    else:
        cursor.execute("""
        UPDATE listing_drafts
        SET status = 'needs_revision'
        WHERE id = ?
        """, (listing["listing_id"],))

    conn.commit()
    conn.close()


def run_compliance_agent():
    listing = get_latest_listing_for_review()

    if not listing:
        print("No listing drafts found for review. Run the Listing Agent first.")
        return

    combined_text = f"""
Product name: {listing["product_name"]}
Product type: {listing["product_type"]}
Design concept: {listing["design_concept"]}
Title: {listing["title"]}
Description: {listing["description"]}
Tags: {listing["tags"]}
"""

    banned_terms_found = basic_banned_term_check(combined_text)

    if banned_terms_found:
        result = {
            "result": "REJECT",
            "risk_level": "high",
            "issues_found": f"Banned/risky terms found: {', '.join(banned_terms_found)}",
            "recommendation": "Revise the product/listing to remove risky trademarked or copyrighted terms."
        }

        save_compliance_result(listing, result)
        print("Compliance failed due to banned terms.")
        print(result)
        return

    prompt = f"""
You are the Compliance Agent for an Etsy print-on-demand shop.

Review this product/listing for risk.

Check for:
- Trademark risk
- Copyright risk
- Celebrity names
- Brand names
- Sports teams
- Song lyrics
- Movie quotes
- Misleading claims
- Copied competitor-style wording
- Anything that could get an Etsy listing flagged

Listing to review:
{combined_text}

Return ONLY valid JSON.
Do not include any explanation before or after the JSON.

Use this exact format:

{{
  "result": "PASS",
  "risk_level": "low",
  "issues_found": "None",
  "recommendation": "Safe to continue."
}}

The result must be one of:
PASS
REVISE
REJECT
"""

    print(f"Compliance Agent is reviewing listing: {listing['title']}")

    response = ask_ollama(prompt)

    if response.startswith("ERROR"):
        print(response)
        return

    print("\nRaw Ollama response:")
    print(response)

    try:
        result = clean_json_response(response)

        if result.get("result") not in ["PASS", "REVISE", "REJECT"]:
            raise ValueError("Result must be PASS, REVISE, or REJECT.")

        save_compliance_result(listing, result)

        print("\nCompliance result saved.")
        print(result)

        if result.get("result") == "PASS":
            print("\nThis listing was added to the approval queue.")

    except Exception as e:
        print("\nCould not save compliance result.")
        print(f"Error: {e}")


if __name__ == "__main__":
    run_compliance_agent()
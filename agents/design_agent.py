import json
import re
import sqlite3
from pathlib import Path

from agents.ollama_helper import ask_ollama
from agents.design_renderer import render_design, sanitize_text


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"

APPROVED_DESIGNS_DIR = BASE_DIR / "designs" / "approved"
APPROVED_DESIGNS_DIR.mkdir(parents=True, exist_ok=True)


ALLOWED_STYLES = [
    "retro_bold",
    "arched_text",
    "minimal_badge",
    "cute_doodle"
]


BAD_PHRASE_PATTERNS = [
    "city map",
    "mandala",
    "within",
    "phase",
    "track",
    "trac",
    "blooming",
    "lorem",
    "ipsum",
]


def get_latest_approved_item():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        approval_queue.id,
        approval_queue.item_id,
        listing_drafts.product_idea_id,
        product_ideas.product_name,
        product_ideas.product_type,
        product_ideas.target_buyer,
        product_ideas.design_concept,
        listing_drafts.title
    FROM approval_queue
    LEFT JOIN listing_drafts ON approval_queue.item_id = listing_drafts.id
    LEFT JOIN product_ideas ON listing_drafts.product_idea_id = product_ideas.id
    WHERE approval_queue.status = 'approved'
      AND approval_queue.action_type = 'create_printify_product'
    ORDER BY approval_queue.id DESC
    LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "approval_id": row[0],
        "listing_draft_id": row[1],
        "product_idea_id": row[2],
        "product_name": row[3],
        "product_type": row[4],
        "target_buyer": row[5],
        "design_concept": row[6],
        "listing_title": row[7],
    }


def clean_json_response(response_text):
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    json_text = response_text[start:end + 1]
    return json.loads(json_text)


def phrase_is_bad(text):
    text_lower = text.lower().strip()

    if len(text_lower) < 3:
        return True

    words = text_lower.split()

    if len(words) > 5:
        return True

    for pattern in BAD_PHRASE_PATTERNS:
        if pattern in text_lower:
            return True

    return False


def normalize_style(style):
    style = (style or "").lower().strip()

    if style not in ALLOWED_STYLES:
        return "retro_bold"

    return style


def save_design_to_database(
    product_idea_id,
    design_file_path,
    main_text,
    sub_text,
    style_notes,
    design_width,
    design_height,
    text_color
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO designs (
        product_idea_id,
        design_file_path,
        main_text,
        sub_text,
        style_notes,
        status,
        design_width,
        design_height,
        text_color
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product_idea_id,
        str(design_file_path),
        main_text,
        sub_text,
        style_notes,
        "needs_review",
        design_width,
        design_height,
        text_color
    ))

    conn.commit()
    conn.close()


def mark_approval_designed(approval_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE approval_queue
    SET status = 'design_created'
    WHERE id = ?
    """, (approval_id,))

    conn.commit()
    conn.close()


def run_design_agent():
    item = get_latest_approved_item()

    if not item:
        print("No approved items found. Run approve_item.py first.")
        return

    prompt = f"""
You are the Design Agent for an Etsy print-on-demand shop.

Create a marketable design plan for this product.

Product name:
{item["product_name"]}

Product type:
{item["product_type"]}

Target buyer:
{item["target_buyer"]}

Design concept:
{item["design_concept"]}

Listing title:
{item["listing_title"]}

Allowed design styles:
retro_bold, arched_text, minimal_badge, cute_doodle

Style guidance:
- retro_bold: best for trendy, funny, teacher, mom, lifestyle, cozy phrases
- arched_text: best for classic giftable sayings and clean lifestyle designs
- minimal_badge: best for simple professional niche designs
- cute_doodle: best for teacher, cozy, bookish, mom, playful, wholesome products

Rules:
- Main text must be 2 to 4 words max.
- The phrase must sound like a real Etsy product someone would buy.
- Avoid abstract, random, vague, or confusing phrases.
- Avoid location phrases unless the product is clearly travel-related.
- The phrase should be giftable, trendy, relatable, funny, cozy, useful, or clearly niche-specific.
- Do not use subtext unless it is very short and helpful.
- No trademarks.
- No celebrities.
- No sports teams.
- No copyrighted characters.
- No song lyrics.
- No brand names.
- Do not use markdown symbols like ** or quotes.

Return ONLY valid JSON.
Do not include any explanation before or after the JSON.

Use this exact format:

{{
  "main_text": "Main design text",
  "sub_text": "",
  "style": "retro_bold",
  "style_notes": "Brief reason for the selected style"
}}
"""

    print(f"Design Agent is creating a Version 4 design for: {item['product_name']}")

    response = ask_ollama(prompt)

    if response.startswith("ERROR"):
        print(response)
        return

    print("\nRaw Ollama response:")
    print(response)

    try:
        design = clean_json_response(response)

        main_text = sanitize_text(design.get("main_text", ""))
        sub_text = sanitize_text(design.get("sub_text", ""))
        style = normalize_style(design.get("style"))
        style_notes = sanitize_text(design.get("style_notes", f"Style selected: {style}"))

        if not main_text:
            print("No main_text returned. Try again.")
            return

        if phrase_is_bad(main_text):
            print(f"Rejected weak or messy phrase: {main_text}")
            print("Run the Design Agent again to generate a better phrase.")
            return

        if sub_text and len(sub_text) > 24:
            sub_text = ""

        safe_filename = item["product_name"].lower().replace(" ", "_").replace("/", "_")
        safe_filename = re.sub(r"[^a-z0-9_\\-]", "", safe_filename)

        output_path = APPROVED_DESIGNS_DIR / f"{safe_filename}_{style}_black.png"

        design_width, design_height = render_design(
            style=style,
            main_text=main_text,
            sub_text=sub_text,
            output_path=output_path,
            text_color="black"
        )

        save_design_to_database(
            product_idea_id=item["product_idea_id"],
            design_file_path=output_path,
            main_text=main_text,
            sub_text=sub_text,
            style_notes=f"{style}: {style_notes}",
            design_width=design_width,
            design_height=design_height,
            text_color="black"
        )

        mark_approval_designed(item["approval_id"])

        print("\nVersion 4 design created successfully.")
        print(f"Main text: {main_text}")
        print(f"Sub text: {sub_text}")
        print(f"Style: {style}")
        print(f"Saved file at: {output_path}")
        print(f"Design size: {design_width} x {design_height}")
        print("\nNext: run the Design Review Agent.")

    except Exception as e:
        print("\nCould not create Version 4 design.")
        print(f"Error: {e}")


if __name__ == "__main__":
    run_design_agent()
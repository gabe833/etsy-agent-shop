import json
import sqlite3
from pathlib import Path

from PIL import Image

from agents.ollama_helper import ask_ollama


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def get_latest_design_for_review():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        designs.id,
        designs.product_idea_id,
        designs.design_file_path,
        designs.main_text,
        designs.sub_text,
        designs.style_notes,
        designs.design_width,
        designs.design_height,
        designs.text_color,
        product_ideas.product_name,
        product_ideas.product_type,
        product_ideas.target_buyer,
        product_ideas.design_concept
    FROM designs
    LEFT JOIN product_ideas ON designs.product_idea_id = product_ideas.id
    WHERE designs.status = 'needs_review'
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
        "sub_text": row[4],
        "style_notes": row[5],
        "design_width": row[6],
        "design_height": row[7],
        "text_color": row[8],
        "product_name": row[9],
        "product_type": row[10],
        "target_buyer": row[11],
        "design_concept": row[12],
    }


def clean_json_response(response_text):
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    json_text = response_text[start:end + 1]
    return json.loads(json_text)


def get_image_measurements(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Design file not found: {file_path}")

    with Image.open(path) as img:
        width, height = img.size

    return width, height


def deterministic_review(design):
    """
    Code-based checks that do not rely on the AI model.
    These catch obvious problems before the AI review.
    """
    issues = []

    main_text = design["main_text"] or ""
    words = main_text.split()

    width, height = get_image_measurements(design["design_file_path"])
    aspect_ratio = width / height if height else 1

    if len(words) > 5:
        issues.append("Main text has too many words.")

    if width < 500 or height < 200:
        issues.append("Design file appears too small.")

    if width > 4200:
        issues.append("Design is extremely wide and may be hard to place.")

    # V4 update:
    # Styled designs can be tall because they include badges, doodles, arcs, or hearts.
    # Tall is only a problem if the design is also very narrow or excessively tall.
    if height > 3600 and aspect_ratio < 0.75:
        issues.append("Design is extremely tall and narrow, which may be hard to place.")

    if height > 4300:
        issues.append("Design height is too large for reliable Printify placement.")

    if "**" in main_text or "*" in main_text:
        issues.append("Design text contains markdown symbols.")

    if len(main_text) > 36:
        issues.append("Main text may be too long for a clean POD design.")

    return issues


def save_review_result(design, result):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO design_reviews (
        design_id,
        product_idea_id,
        result,
        readability_score,
        marketability_score,
        niche_fit_score,
        placement_score,
        issues_found,
        recommendation
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        design["design_id"],
        design["product_idea_id"],
        result.get("result"),
        result.get("readability_score"),
        result.get("marketability_score"),
        result.get("niche_fit_score"),
        result.get("placement_score"),
        result.get("issues_found"),
        result.get("recommendation")
    ))

    if result.get("result") == "PASS":
        new_status = "review_passed"
    else:
        new_status = "review_failed"

    cursor.execute("""
    UPDATE designs
    SET status = ?,
        review_notes = ?
    WHERE id = ?
    """, (
        new_status,
        result.get("issues_found"),
        design["design_id"]
    ))

    conn.commit()
    conn.close()


def run_design_review_agent():
    design = get_latest_design_for_review()

    if not design:
        print("No designs need review. Run the Design Agent first.")
        return

    print(f"Reviewing design: {design['main_text']}")

    # Refresh measurements from actual image file
    actual_width, actual_height = get_image_measurements(design["design_file_path"])
    design["design_width"] = actual_width
    design["design_height"] = actual_height

    deterministic_issues = deterministic_review(design)

    if deterministic_issues:
        result = {
            "result": "REVISE",
            "readability_score": 5,
            "marketability_score": 5,
            "niche_fit_score": 5,
            "placement_score": 4,
            "issues_found": "; ".join(deterministic_issues),
            "recommendation": "Regenerate or revise the design before sending to Printify."
        }

        save_review_result(design, result)

        print("\nDesign failed deterministic review.")
        print(result)
        return

    prompt = f"""
You are the Design Review Agent for an Etsy print-on-demand shop.

Review this design before it is uploaded to Printify.

Product name:
{design["product_name"]}

Product type:
{design["product_type"]}

Target buyer:
{design["target_buyer"]}

Original design concept:
{design["design_concept"]}

Main design text:
{design["main_text"]}

Sub text:
{design["sub_text"]}

Style notes:
{design["style_notes"]}

Design image size:
{design["design_width"]} x {design["design_height"]}

Text color:
{design["text_color"]}

Review the design for:
- Readability
- Marketability
- Whether someone would actually buy it
- Whether it matches the target buyer
- Whether the phrase sounds random or generic
- Whether the style choice makes sense
- Whether the design is too plain to compete on Etsy
- Whether it is safe from trademark/copyright concerns
- Whether it should go to Printify

Scoring:
- readability_score: 1 to 10
- marketability_score: 1 to 10
- niche_fit_score: 1 to 10
- placement_score: 1 to 10

Pass only if:
- readability_score >= 8
- marketability_score >= 7
- niche_fit_score >= 7
- placement_score >= 7
- style is more than plain text
- phrase is clear and sellable
- no obvious trademark/copyright risk

Return ONLY valid JSON.
Do not include any explanation before or after the JSON.

Use this exact format:

{{
  "result": "PASS",
  "readability_score": 9,
  "marketability_score": 8,
  "niche_fit_score": 8,
  "placement_score": 9,
  "issues_found": "None",
  "recommendation": "Safe to send to Printify."
}}

The result must be one of:
PASS
REVISE
REJECT
"""

    response = ask_ollama(prompt)

    if response.startswith("ERROR"):
        print(response)
        return

    print("\nRaw Ollama response:")
    print(response)

    try:
        result = clean_json_response(response)

        if result.get("result") not in ["PASS", "REVISE", "REJECT"]:
            raise ValueError("Review result must be PASS, REVISE, or REJECT.")

        save_review_result(design, result)

        print("\nDesign review saved.")
        print(result)

        if result.get("result") == "PASS":
            print("\nDesign passed review and is ready for Printify.")
        else:
            print("\nDesign did not pass. Regenerate or revise before Printify.")

    except Exception as e:
        print("\nCould not save design review.")
        print(f"Error: {e}")


if __name__ == "__main__":
    run_design_review_agent()
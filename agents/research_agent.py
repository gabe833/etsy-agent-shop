import json
import sqlite3
from pathlib import Path

from agents.ollama_helper import ask_ollama


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def clean_json_response(response_text):
    """
    Tries to extract JSON from Ollama's response.
    Sometimes local models add extra text, so this helps clean it up.
    """

    start = response_text.find("[")
    end = response_text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No JSON array found in the model response.")

    json_text = response_text[start:end + 1]
    return json.loads(json_text)


def save_niches_to_database(niches):
    """
    Saves niche ideas into the SQLite database.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for niche in niches:
        cursor.execute("""
        INSERT INTO niches (
            niche_name,
            target_buyer,
            demand_score,
            competition_score,
            ease_score,
            risk_score,
            notes,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            niche.get("niche_name"),
            niche.get("target_buyer"),
            niche.get("demand_score"),
            niche.get("competition_score"),
            niche.get("ease_score"),
            niche.get("risk_score"),
            niche.get("notes"),
            "new"
        ))

    conn.commit()
    conn.close()


def run_research_agent():
    """
    Asks Ollama for Etsy print-on-demand niche ideas and saves them to the database.
    """

    prompt = """
You are the Market Research Agent for an Etsy print-on-demand shop.

Find 5 original Etsy print-on-demand niche ideas.

Rules:
- Avoid Disney, Bluey, Barbie, Taylor Swift, celebrities, sports teams, college names, brand names, movie quotes, song lyrics, and trademarked phrases.
- Focus on products that could work on t-shirts, sweatshirts, mugs, tote bags, or stickers.
- Keep ideas simple enough for beginner print-on-demand designs.
- Do not copy competitor designs.
- Do not use copyrighted characters.

Return ONLY valid JSON.
Do not include any explanation before or after the JSON.

Use this exact format:

[
  {
    "niche_name": "Example niche",
    "target_buyer": "Example buyer",
    "demand_score": 8,
    "competition_score": 5,
    "ease_score": 9,
    "risk_score": 2,
    "notes": "Short reason this niche could work."
  }
]
"""

    print("Research Agent is asking Ollama for niche ideas...")

    response = ask_ollama(prompt)

    if response.startswith("ERROR"):
        print(response)
        return

    print("\nRaw Ollama response:")
    print(response)

    try:
        niches = clean_json_response(response)
        save_niches_to_database(niches)
        print(f"\nSaved {len(niches)} niche ideas to the database.")

    except Exception as e:
        print("\nCould not save niches.")
        print(f"Error: {e}")
        print("\nThe model may not have returned clean JSON. Try running it again.")


if __name__ == "__main__":
    run_research_agent()
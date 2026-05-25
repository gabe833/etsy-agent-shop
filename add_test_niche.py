import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

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
    "Kindergarten teacher gifts",
    "Kindergarten teachers",
    8,
    6,
    9,
    2,
    "Good starter niche because it matches your background and can work for shirts, mugs, and tote bags.",
    "new"
))

conn.commit()
conn.close()

print("Test niche added successfully.")
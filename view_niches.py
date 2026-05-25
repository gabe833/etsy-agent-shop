import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT id, niche_name, target_buyer, demand_score, competition_score, ease_score, risk_score, status
FROM niches
""")

rows = cursor.fetchall()

print("Saved niches:")
for row in rows:
    print(row)

conn.close()
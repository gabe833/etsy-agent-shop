import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT 
    product_ideas.id,
    niches.niche_name,
    product_ideas.product_name,
    product_ideas.product_type,
    product_ideas.target_buyer,
    product_ideas.suggested_price,
    product_ideas.risk_level,
    product_ideas.status
FROM product_ideas
LEFT JOIN niches ON product_ideas.niche_id = niches.id
ORDER BY product_ideas.id DESC
""")

rows = cursor.fetchall()

print("Saved product ideas:")
for row in rows:
    print(row)

conn.close()
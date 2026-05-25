import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT 
    listing_drafts.id,
    product_ideas.product_name,
    listing_drafts.title,
    listing_drafts.suggested_price,
    listing_drafts.tags,
    listing_drafts.status
FROM listing_drafts
LEFT JOIN product_ideas ON listing_drafts.product_idea_id = product_ideas.id
ORDER BY listing_drafts.id DESC
""")

rows = cursor.fetchall()

print("Saved listing drafts:")
for row in rows:
    print("\n---")
    print("Listing ID:", row[0])
    print("Product:", row[1])
    print("Title:", row[2])
    print("Price:", row[3])
    print("Tags:", row[4])
    print("Status:", row[5])

conn.close()
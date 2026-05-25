import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT 
    designs.id,
    product_ideas.product_name,
    designs.design_file_path,
    designs.main_text,
    designs.sub_text,
    designs.status,
    designs.created_at
FROM designs
LEFT JOIN product_ideas ON designs.product_idea_id = product_ideas.id
ORDER BY designs.id DESC
""")

rows = cursor.fetchall()

print("Saved designs:")

for row in rows:
    print("\n---")
    print("Design ID:", row[0])
    print("Product:", row[1])
    print("File:", row[2])
    print("Main Text:", row[3])
    print("Sub Text:", row[4])
    print("Status:", row[5])
    print("Created:", row[6])

conn.close()
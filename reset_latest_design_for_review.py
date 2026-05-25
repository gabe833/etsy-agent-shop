import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT id, main_text, design_file_path, status, design_width, design_height
FROM designs
ORDER BY id DESC
LIMIT 1
""")

row = cursor.fetchone()

if not row:
    print("No designs found.")
    conn.close()
    exit()

design_id, main_text, design_file_path, status, width, height = row

print("Latest design:")
print("Design ID:", design_id)
print("Text:", main_text)
print("File:", design_file_path)
print("Current status:", status)
print("Size:", width, "x", height)

confirm = input("\nSet this design back to needs_review? y/n: ")

if confirm.lower() != "y":
    print("No changes made.")
    conn.close()
    exit()

cursor.execute("""
UPDATE designs
SET status = 'needs_review'
WHERE id = ?
""", (design_id,))

conn.commit()
conn.close()

print("Design reset to needs_review. Now run: python main.py design_review")
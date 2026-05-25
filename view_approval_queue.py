import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT 
    id,
    action_type,
    item_type,
    item_id,
    summary,
    risk_level,
    status,
    approved,
    created_at
FROM approval_queue
ORDER BY id DESC
""")

rows = cursor.fetchall()

print("Approval Queue:")
for row in rows:
    print("\n---")
    print("Approval ID:", row[0])
    print("Action:", row[1])
    print("Item Type:", row[2])
    print("Item ID:", row[3])
    print("Summary:", row[4])
    print("Risk Level:", row[5])
    print("Status:", row[6])
    print("Approved:", row[7])
    print("Created:", row[8])

conn.close()
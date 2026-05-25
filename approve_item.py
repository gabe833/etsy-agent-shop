import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT id, action_type, item_type, item_id, summary, risk_level
FROM approval_queue
WHERE status = 'pending'
ORDER BY id ASC
""")

items = cursor.fetchall()

if not items:
    print("No pending approvals.")
    conn.close()
    exit()

print("Pending approvals:")

for item in items:
    print("\n---")
    print("Approval ID:", item[0])
    print("Action:", item[1])
    print("Item Type:", item[2])
    print("Item ID:", item[3])
    print("Summary:", item[4])
    print("Risk Level:", item[5])

approval_id = input("\nEnter the Approval ID to approve, or type 'q' to quit: ")

if approval_id.lower() == "q":
    print("No action taken.")
    conn.close()
    exit()

cursor.execute("""
UPDATE approval_queue
SET approved = 1,
    status = 'approved',
    approved_at = ?
WHERE id = ?
""", (datetime.now(), approval_id))

conn.commit()
conn.close()

print(f"Approval ID {approval_id} approved.")
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT
    design_reviews.id,
    designs.main_text,
    product_ideas.product_name,
    design_reviews.result,
    design_reviews.readability_score,
    design_reviews.marketability_score,
    design_reviews.niche_fit_score,
    design_reviews.placement_score,
    design_reviews.issues_found,
    design_reviews.recommendation,
    design_reviews.created_at
FROM design_reviews
LEFT JOIN designs ON design_reviews.design_id = designs.id
LEFT JOIN product_ideas ON design_reviews.product_idea_id = product_ideas.id
ORDER BY design_reviews.id DESC
""")

rows = cursor.fetchall()

print("Design Reviews:")

for row in rows:
    print("\n---")
    print("Review ID:", row[0])
    print("Design Text:", row[1])
    print("Product:", row[2])
    print("Result:", row[3])
    print("Readability:", row[4])
    print("Marketability:", row[5])
    print("Niche Fit:", row[6])
    print("Placement:", row[7])
    print("Issues:", row[8])
    print("Recommendation:", row[9])
    print("Created:", row[10])

conn.close()
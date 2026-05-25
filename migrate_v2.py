import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "shop.db"


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column[1] == column_name for column in columns)


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Stores design review results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS design_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        design_id INTEGER,
        product_idea_id INTEGER,
        result TEXT,
        readability_score INTEGER,
        marketability_score INTEGER,
        niche_fit_score INTEGER,
        placement_score INTEGER,
        issues_found TEXT,
        recommendation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (design_id) REFERENCES designs(id),
        FOREIGN KEY (product_idea_id) REFERENCES product_ideas(id)
    )
    """)

    # Add extra columns to designs table if they do not exist
    if not column_exists(cursor, "designs", "review_notes"):
        cursor.execute("ALTER TABLE designs ADD COLUMN review_notes TEXT")

    if not column_exists(cursor, "designs", "design_width"):
        cursor.execute("ALTER TABLE designs ADD COLUMN design_width INTEGER")

    if not column_exists(cursor, "designs", "design_height"):
        cursor.execute("ALTER TABLE designs ADD COLUMN design_height INTEGER")

    if not column_exists(cursor, "designs", "text_color"):
        cursor.execute("ALTER TABLE designs ADD COLUMN text_color TEXT")

    conn.commit()
    conn.close()

    print("Version 2 migration complete.")


if __name__ == "__main__":
    run_migration()
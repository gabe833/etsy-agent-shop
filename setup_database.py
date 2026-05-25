import sqlite3
from pathlib import Path

# Create path to the data folder
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "shop.db"

# Make sure data folder exists
DATA_DIR.mkdir(exist_ok=True)

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Stores the business rules for your automation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_name TEXT NOT NULL UNIQUE,
        setting_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Stores niche ideas found by the Research Agent
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS niches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT NOT NULL,
        target_buyer TEXT,
        demand_score INTEGER,
        competition_score INTEGER,
        ease_score INTEGER,
        risk_score INTEGER,
        notes TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Stores specific product ideas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_id INTEGER,
        product_name TEXT NOT NULL,
        product_type TEXT,
        target_buyer TEXT,
        design_concept TEXT,
        suggested_price REAL,
        risk_level TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (niche_id) REFERENCES niches(id)
    )
    """)

    # Stores generated design files
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS designs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_idea_id INTEGER,
        design_file_path TEXT,
        main_text TEXT,
        sub_text TEXT,
        style_notes TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_idea_id) REFERENCES product_ideas(id)
    )
    """)

    # Stores Etsy/Printify listing drafts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listing_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_idea_id INTEGER,
        title TEXT,
        description TEXT,
        tags TEXT,
        suggested_price REAL,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_idea_id) REFERENCES product_ideas(id)
    )
    """)

    # Stores compliance reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compliance_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_idea_id INTEGER,
        listing_draft_id INTEGER,
        result TEXT,
        risk_level TEXT,
        issues_found TEXT,
        recommendation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_idea_id) REFERENCES product_ideas(id),
        FOREIGN KEY (listing_draft_id) REFERENCES listing_drafts(id)
    )
    """)

    # Stores anything that needs your approval
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approval_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        item_type TEXT,
        item_id INTEGER,
        summary TEXT,
        risk_level TEXT,
        status TEXT DEFAULT 'pending',
        approved INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP
    )
    """)

    # Stores Printify products after creation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS printify_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_idea_id INTEGER,
        printify_product_id TEXT,
        printify_shop_id TEXT,
        title TEXT,
        status TEXT DEFAULT 'created',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_idea_id) REFERENCES product_ideas(id)
    )
    """)

    # Stores Etsy listing info
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS etsy_listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_idea_id INTEGER,
        etsy_listing_id TEXT,
        etsy_url TEXT,
        title TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_idea_id) REFERENCES product_ideas(id)
    )
    """)

    # Stores order info from Printify/Etsy
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_source TEXT,
        external_order_id TEXT,
        customer_name TEXT,
        product_name TEXT,
        order_status TEXT,
        fulfillment_status TEXT,
        tracking_number TEXT,
        issue_flag INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Stores customer message drafts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        customer_name TEXT,
        message_received TEXT,
        drafted_reply TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """)

    # Stores logs from each agent
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        task_type TEXT,
        input_summary TEXT,
        output_summary TEXT,
        status TEXT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Add default settings
    default_settings = {
        "auto_publish": "false",
        "max_listings_per_day": "1",
        "allowed_products": "t-shirt,sweatshirt,mug",
        "minimum_profit_margin": "0.35",
        "auto_send_customer_messages": "false",
        "auto_refund": "false",
        "trademark_check_required": "true"
    }

    for name, value in default_settings.items():
        cursor.execute("""
        INSERT OR IGNORE INTO settings (setting_name, setting_value)
        VALUES (?, ?)
        """, (name, value))

    conn.commit()
    conn.close()

    print(f"Database created successfully at: {DB_PATH}")

if __name__ == "__main__":
    create_database()
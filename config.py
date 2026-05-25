import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "shop.db"

DESIGNS_DIR = BASE_DIR / "designs"
APPROVED_DESIGNS_DIR = DESIGNS_DIR / "approved"
UPLOADED_DESIGNS_DIR = DESIGNS_DIR / "uploaded"

PRODUCT_CATALOG_PATH = DATA_DIR / "product_catalog.json"

load_dotenv(BASE_DIR / ".env")

PRINTIFY_API_TOKEN = os.getenv("PRINTIFY_API_TOKEN")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")
PRINTIFY_API_BASE = "https://api.printify.com/v1"
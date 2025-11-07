import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("MongoDB")

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    logger.error("❌ MONGO_URI belum di set di .env!")
    raise SystemExit("MONGO_URI not found in environment variables")

client = AsyncIOMotorClient(MONGO_URI)

# Nama database utama
db = client["management_bot"]

# Collections
users_col = db["users"]
partners_col = db["partners"]
backup_col = db["backups"]
payments_col = db["payments"]
products_col = db["products"]

logger.info("✅ MongoDB module loaded")

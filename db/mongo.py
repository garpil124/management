import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("MongoDB")

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    logger.error("❌ MONGO_URI belum di set di .env!")
    raise SystemExit("MONGO_URI not found in environment variables")

client: AsyncIOMotorClient = None
db = None

# Collections:
users_col = None
partners_col = None
backup_col = None
payments_col = None
products_col = None
orders_col = None  # ✅ WAJIB ditambah biar handler user ga error


async def init_mongo(uri: str):
    global client, db
    global users_col, partners_col, backup_col, payments_col, products_col, orders_col

    logger.info("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(uri)
    db = client["management_bot"]

    users_col = db["users"]
    partners_col = db["partners"]
    backup_col = db["backups"]
    payments_col = db["payments"]
    products_col = db["products"]
    orders_col = db["orders"]  # ✅ collection baru buat order user

    logger.info("✅ MongoDB connected successfully!")


def get_client():
    return client

def get_db():
    return db

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

logger = logging.getLogger("MongoDB")

client: AsyncIOMotorClient = None
db = None

users_col = None
partners_col = None
backup_col = None
payments_col = None
products_col = None
orders_col = None
subowners_col = None

def init_mongo():
    global client, db
    global users_col, partners_col, backup_col, payments_col, products_col, orders_col, subowners_col

    logger.info("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["management_bot"]

    users_col = db["users"]
    partners_col = db["partners"]
    subowners_col = db["subowners"]
    backup_col = db["backups"]
    payments_col = db["payments"]
    products_col = db["products"]
    orders_col = db["orders"]

    logger.info("✅ MongoDB connected")

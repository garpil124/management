import logging
from db.mongo import users_col, partners_col, backup_col, payments_col, products_col

logger = logging.getLogger("InitDB")

async def init_db_indexes():
    try:
        # Users
        await users_col.create_index("user_id", unique=True)

        # Partners (sub-bot / sub-owner)
        await partners_col.create_index("bot_token")
        await partners_col.create_index("owner_id")

        # Payments
        await payments_col.create_index("invoice_id", unique=True)
        await payments_col.create_index("user_id")

        # Products
        await products_col.create_index("product_id", unique=True)

        # Backups
        await backup_col.create_index("created_at")

        logger.info("✅ Semua index database berhasil dibuat!")
    except Exception as e:
        logger.error(f"❌ Gagal init index MongoDB: {e}")

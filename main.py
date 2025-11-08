import asyncio
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# ===== Project Imports =====
from config import BOT_TOKEN, API_ID, API_HASH, MONGO_URI
from pyrogram import Client
from db.mongo import init_mongo
from utils.backup import start_auto_backup
# NOTE: kamu belum kirim scheduler, kalau belum ada harus dimatiin dulu

# Handlers sesuai folder kamu
from handlers.help import register_help
from handlers.start import register_start
from handlers.owner import register_owner
from handlers.subowner import register_subowner
from handlers.catalog import register_catalog
from handlers.payments import register_payment
from handlers.tagall import register_tagall

# ===== Logging Setup =====
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("ManagementBot")

# ===== Pyrogram Client =====
app = Client(
    name="management_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ===== Register Semua Handlers =====
def register_all_handlers():
    register_start(app)
    register_help(app)
    register_owner(app)
    register_subowner(app)
    register_catalog(app)
    register_payment(app)
    register_tagall(app)
    logger.info("✅ All handlers registered successfully!")

# ===== MAIN RUNNER =====
async def main():
    logger.info("🚀 Starting bot...")

    # 1. Connect ke Mongo
    await init_mongo(MONGO_URI)

    # 2. Register semua handler
    register_all_handlers()

    # 3. Auto backup (scheduler kamu aku nonaktifin dulu karena belum ada filenya)
    start_auto_backup()

    # 4. Jalankan bot
    try:
        await app.start()
        logger.info("🤖 Bot is online & running!")
        await asyncio.Event().wait()  # biar bot tetap hidup
    except Exception as e:
        logger.critical(f"🔥 Bot crashed: {e}")
        sys.exit(1)

# ===== Program Entry Point =====
if name == "main":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("🛑 Bot stopped manually.")
    except Exception as e:
        logger.error(f"⚠️ Unexpected error: {e}")

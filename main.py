import asyncio
import logging
import sys
from pyrogram import Client

from config import (
    BOT_TOKEN, API_ID, API_HASH,
    OWNER_ID, CREATOR_NAME, LOG_CHAT_ID,
    MONGO_URI, DB_NAME
)

from db.mongo import connect_db, get_db
from utils.scheduler import start_scheduler
from utils.backup import start_auto_backup

# Import handler modules biar kebaca Pyrogram
import handlers.help
import handlers.owner
import handlers.subowner
import handlers.catalog
import handlers.payment
import handlers.premium

# Logging biar keliatan enak
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ManagerBot")


async def on_start():
    """Jalan saat bot hidup"""
    logger.info("🚀 BOT SEDANG START...")

    # 1) Connect MongoDB
    await connect_db(MONGO_URI, DB_NAME)
    db = get_db()
    logger.info("✅ MongoDB Connected!")

    # 2) Start scheduler
    start_scheduler()
    logger.info("✅ Scheduler Running!")

    # 3) Start auto backup
    start_auto_backup()
    logger.info("✅ Auto Backup Active!")

    # 4) Kirim notifikasi ke log chat
    if LOG_CHAT_ID:
        try:
            await app.send_message(
                LOG_CHAT_ID,
                f"🤖 BOT RUNNING\n"
                f"👑 Owner: {OWNER_ID}\n"
                f"🧠 Creator: {CREATOR_NAME}"
            )
        except:
            logger.warning("⚠️ Gagal kirim ke LOG_CHAT_ID")

    logger.info("🔥 SEMUA MODULE SIAP. BOT LIVE!")


async def on_stop():
    logger.info("🛑 Bot berhenti...")


# Setup Pyrogram Client
app = Client(
    name="ManagerBot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    plugins=dict(root="handlers")  # <- otomatis load semua handler
)

app.on_startup(on_start)
app.on_shutdown(on_stop)


if name == "main":
    try:
        logger.info("▶ Bot running...")
        app.run()
    except KeyboardInterrupt:
        logger.info("⏹ Bot dimatiin manual.")
    except Exception as e:
        logger.critical(f"💀 BOT CRASH: {e}", exc_info=True)

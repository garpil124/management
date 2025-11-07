import sys
import logging
import asyncio
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load ENV dulu
load_dotenv()

# Logging setup biar debug enak
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ManagementBot")

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Unknown")

if not BOT_TOKEN or not MONGO_URI:
    logger.critical("❌ BOT_TOKEN atau MONGO_URI belum di set di .env")
    sys.exit(1)

# Init bot main
app = Client(
    "management_bot",
    bot_token=BOT_TOKEN
)

# MongoDB
mongodb = AsyncIOMotorClient(MONGO_URI)
db = mongodb["management_bot"]

async def init_database():
    try:
        # Test ping biar yakin connect
        await mongodb.admin.command("ping")
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.critical(f"❌ MongoDB gagal connect: {e}")
        sys.exit(1)

# Auto load handlers biar gak import satu-satu manual
def load_handlers():
    import glob, importlib
    files = glob.glob("handlers/*.py")
    for file in files:
        name = file.replace("/", ".").replace("\\", ".").replace(".py", "")
        if "init" not in name:
            importlib.import_module(name)
            logger.info(f"📌 Handler loaded: {name}")

async def start_scheduler():
    try:
        from utils.scheduler import start_scheduler
        await start_scheduler()
        logger.info("✅ Scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler error: {e}")

async def start_auto_backup():
    try:
        from utils.backup import auto_backup
        asyncio.create_task(auto_backup())
        logger.info("✅ Auto backup task running")
    except Exception as e:
        logger.warning(f"⚠️ Auto backup error: {e}")

async def main():
    logger.info("🚀 Bot starting...")

    await init_database()
    load_handlers()
    await start_scheduler()
    await start_auto_backup()

    await app.start()
    me = await app.get_me()
    logger.info(f"🤖 Bot aktif: {me.first_name} (@{me.username})")
    logger.info(f"👑 Creator: {CREATOR_NAME}")
    logger.info("✅ Bot siap digunakan!")

    await idle()

from pyrogram import idle

if name == "main":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot dimatikan manual")

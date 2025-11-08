import asyncio
import logging
import sys
from dotenv import load_dotenv
load_dotenv()

from config import BOT_TOKEN, API_ID, API_HASH
from pyrogram import Client
from db.mongo import init_mongo
from utils.backup import start_auto_backup
from utils.scheduler import start_scheduler
from handlers import register_all_handlers

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ManagementBot")

app = Client(
    name="management_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    logger.info("🚀 Starting bot...")
    # init mongo
    try:
        await init_mongo()
    except Exception as e:
        logger.critical("Mongo init failed: %s", e)
        return

    # register handlers
    register_all_handlers(app)
    # start scheduler
    start_scheduler()
    # start backup asynchronously (non-blocking)
    asyncio.create_task(start_auto_backup())

    try:
        await app.start()
        logger.info("✅ Bot is online & running")
        await asyncio.Event().wait()
    except Exception as e:
        logger.critical("🔥 Bot crashed: %s", e)
        raise

if name == "main":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("🛑 Bot stopped manually.")
    except Exception as e:
        logger.exception("Unexpected error: %s", e)

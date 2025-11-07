import asyncio
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI
from db.mongo import init_mongo

# Import handlers
from handlers.start import start_handler
from handlers.help import help_handler
from handlers.owner import owner_handler
from handlers.subowner import subowner_handler
from handlers.tagall import tagall_handler
from handlers.product import product_handler
from handlers.payment import payment_handler

# Import utils
from utils.scheduler import run_scheduler
from utils.backup import auto_backup

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s -> %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("MAIN")

# Pyrogram Client
bot = Client(
    "ManagementBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4
)

async def register_handlers():
    log.info("🔁 Registering handlers...")

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)
    bot.add_handler(owner_handler)
    bot.add_handler(subowner_handler)
    bot.add_handler(tagall_handler)
    bot.add_handler(product_handler)
    bot.add_handler(payment_handler)

    log.info("✅ All handlers registered!")

async def start_services():
    log.info("🚀 Starting services...")

    # Connect Mongo
    await init_mongo(MONGO_URI)

    # Load handlers
    await register_handlers()

    # Start scheduler
    asyncio.create_task(run_scheduler())

    # Start auto backup
    asyncio.create_task(auto_backup())

    log.info("🔥 All services started!")

async def main():
    async with bot:
        await start_services()
        log.info("🤖 Bot is running...")
        await asyncio.Event().wait()

if name == "main":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.warning("🛑 Bot stopped manually")
    except Exception as err:
        log.critical(f"💀 Fatal error: {err}")

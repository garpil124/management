# main.py
import sys
import logging
import asyncio
from pyrogram import Client, errors
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, LOGGER_ID
from db.connector import connect_db
from utils.logger import logger

# Biar handler auto ke-load
import handlers  # noqa

async def main():
    logger.info("🚀 Starting bot...")

    # connect database
    try:
        await connect_db(MONGO_URI)
        logger.info("✅ MongoDB Connected")
    except Exception as e:
        logger.critical(f"❌ MongoDB Failed: {e}")
        sys.exit(1)

    # start pyrogram bot
    app = Client(
        "garfield_store_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workers=20
    )

    try:
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot started as @{me.username} ({me.id})")

        if LOGGER_ID:
            try:
                await app.send_message(LOGGER_ID, f"✅ Bot Online: @{me.username}")
            except errors.RPCError as e:
                logger.warning(f"⚠ Cannot send log to LOGGER_ID: {e}")

        await idle()

    except Exception as e:
        logger.critical(f"🔥 Fatal error start bot: {e}")
        sys.exit(1)

    await app.stop()
    logger.info("🛑 Bot Stopped.")


from pyrogram import idle

if name == "main":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🟡 Bot stopped manually")
    except Exception as e:
        logger.critical(f"🔥 Unexpected crash: {e}")
        sys.exit(1)

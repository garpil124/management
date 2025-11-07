import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from db.mongo import client as mongo_client
import sys

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Bot")

# Init bot client
app = Client(
    "management_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="handlers")  # Load semua file dalam folder handlers otomatis
)

# Test koneksi MongoDB
try:
    mongo_client.admin.command("ping")
    logger.info("✅ MongoDB Connected")
except Exception as e:
    logger.error(f"❌ MongoDB Error: {e}")
    sys.exit(1)

# Run bot
if name == "main":
    logger.info("🚀 Bot is starting...")
    app.run()

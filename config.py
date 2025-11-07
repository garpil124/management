import os
from dotenv import load_dotenv

load_dotenv()

# === Telegram Config ===
BOT_TOKEN   = os.getenv("BOT_TOKEN")
API_ID      = int(os.getenv("API_ID"))
API_HASH    = os.getenv("API_HASH")

# === Owner & Logs ===
OWNER_ID    = int(os.getenv("OWNER_ID"))
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID"))

# === Database ===
MONGO_URI   = os.getenv("MONGO_URI")

# === Info Tambahan ===
CREATOR_NAME = os.getenv("CREATOR_NAME", "Unknown")
BACKUP_FOLDER = os.getenv("BACKUP_FOLDER", "backups")

# Validasi biar langsung error kalo ada yang kosong
required = {
    "BOT_TOKEN": BOT_TOKEN,
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "OWNER_ID": OWNER_ID,
    "LOG_CHAT_ID": LOG_CHAT_ID,
    "MONGO_URI": MONGO_URI
}

for key, value in required.items():
    if not value:
        raise RuntimeError(f"❌ Config error: {key} belum di set di .env")

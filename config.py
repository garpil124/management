import os
from dotenv import load_dotenv

load_dotenv()

try:
    API_ID = int(os.getenv("API_ID"))  
except:
    raise SystemExit("❌ API_ID invalid atau belum di set di .env")

API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_HASH or not BOT_TOKEN:
    raise SystemExit("❌ API_HASH atau BOT_TOKEN belum di set di .env")

try:
    OWNER_ID = int(os.getenv("OWNER_ID"))
except:
    raise SystemExit("❌ OWNER_ID invalid atau belum di set di .env")

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise SystemExit("❌ MONGO_URI belum di set di .env")

try:
    LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))
except:
    LOG_CHAT_ID = 0

# Backup & scheduler settings
BACKUP_FOLDER = os.getenv("BACKUP_FOLDER", "backups")
BACKUP_HOUR = int(os.getenv("BACKUP_HOUR", "23"))
BACKUP_MINUTE = int(os.getenv("BACKUP_MINUTE", "55"))
AUTO_RESTART_HOUR = int(os.getenv("AUTO_RESTART_HOUR", "0"))
AUTO_RESTART_MINUTE = int(os.getenv("AUTO_RESTART_MINUTE", "0"))

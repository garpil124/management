import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

MONGO_URI = os.getenv("MONGO_URI", "")
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0") or 0)

BACKUP_FOLDER = os.getenv("BACKUP_FOLDER", "backups")
BACKUP_HOUR = int(os.getenv("BACKUP_HOUR", "23"))
BACKUP_MINUTE = int(os.getenv("BACKUP_MINUTE", "55"))
AUTO_RESTART_HOUR = int(os.getenv("AUTO_RESTART_HOUR", "0"))
AUTO_RESTART_MINUTE = int(os.getenv("AUTO_RESTART_MINUTE", "0"))

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────
# 🛡 SAFE GET ENV FUNCTIONS
# ─────────────────────────────
def get_env(name, required=True, default=None):
    value = os.getenv(name, default)
    if required and not value:
        raise SystemExit(f"❌ {name} belum di set di .env")
    return value

def get_env_int(name, required=True, default=None):
    try:
        return int(os.getenv(name, default))
    except:
        if required:
            raise SystemExit(f"❌ {name} invalid atau belum di set di .env")
        return default

# ─────────────────────────────
# 🤖 BOT CORE CONFIG
# ─────────────────────────────
API_ID    = get_env_int("API_ID")
API_HASH  = get_env("API_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")

# ─────────────────────────────
# 👑 OWNER / CREATOR CONFIG
# ─────────────────────────────
# Bisa multi owner: 123456,7891011,121314
OWNER_ID  = get_env("OWNER_ID")
OWNER_IDS = [int(x) for x in OWNER_ID.split(",")]

CREATOR_NAME = get_env("CREATOR_NAME", required=False, default="@yourusername")

# ─────────────────────────────
# 🗄 DATABASE
# ─────────────────────────────
MONGO_URI = get_env("MONGO_URI")

# ─────────────────────────────
# 📌 LOGGING
# ─────────────────────────────
LOG_CHAT_ID = get_env_int("LOG_CHAT_ID", required=False, default=0)

# ─────────────────────────────
# 💾 BACKUP & RESTART SETTINGS
# ─────────────────────────────
BACKUP_FOLDER = get_env("BACKUP_FOLDER", required=False, default="backups")
BACKUP_HOUR   = get_env_int("BACKUP_HOUR", required=False, default=23)
BACKUP_MINUTE = get_env_int("BACKUP_MINUTE", required=False, default=55)

AUTO_RESTART_HOUR   = get_env_int("AUTO_RESTART_HOUR", required=False, default=0)
AUTO_RESTART_MINUTE = get_env_int("AUTO_RESTART_MINUTE", required=False, default=0)

# ─────────────────────────────
# ⚙ AUTO CHECK & INIT
# ─────────────────────────────
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)
    print(f"✅ Backup folder dibuat otomatis: {BACKUP_FOLDER}")

print("""
╔═══════════════════════════════════════╗
║ ✅ CONFIG LOADED SUCCESSFULLY (HEDON) ║
╠═══════════════════════════════════════╣
║ OWNER IDs : %s
║ Creator  : %s
║ Backup   : %s (Jam %s:%s)
║ Restart  : %s:%s
╚═══════════════════════════════════════╝
""" % (OWNER_IDS, CREATOR_NAME, BACKUP_FOLDER, BACKUP_HOUR, BACKUP_MINUTE, AUTO_RESTART_HOUR, AUTO_RESTART_MINUTE))

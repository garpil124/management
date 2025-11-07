import os
from dotenv import load_dotenv

load_dotenv()

# === Bot Utama ===
BOT_TOKEN      = os.getenv("BOT_TOKEN")
API_ID         = int(os.getenv("API_ID", 0))
API_HASH       = os.getenv("API_HASH")

# === Owner & Identitas ===
OWNER_ID       = int(os.getenv("OWNER_ID", 0))
CREATOR_NAME   = os.getenv("CREATOR_NAME", "Unknown")

# === Database ===
MONGO_URI      = os.getenv("MONGO_URI")
DB_NAME        = os.getenv("DB_NAME", "telegram_manager")

# === Logs & Monitor ===
LOG_CHAT_ID    = int(os.getenv("LOG_CHAT_ID", 0))

# === Payment (QRIS Manual) ===
PAYMENT_QRIS_DANA  = os.getenv("PAYMENT_QRIS_DANA", "")
PAYMENT_QRIS_GOPAY = os.getenv("PAYMENT_QRIS_GOPAY", "")

# === Backup Config ===
BACKUP_FOLDER  = os.getenv("BACKUP_FOLDER", "backups")

# === Premium Setting ===
DEFAULT_PREMIUM_DAYS = 30  # 30 hari otomatis

# --- Validasi wajib ---
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN belum di set di .env!")
if API_ID == 0 or not API_HASH:
    raise RuntimeError("❌ API_ID/API_HASH belum di set di .env!")
if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI belum di set di .env!")

print("✅ Config berhasil dimuat!")

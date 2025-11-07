import os
from dotenv import load_dotenv

load_dotenv()

# ================= BOT SETTINGS =================
API_ID       = int(os.getenv("API_ID", 0))
API_HASH     = os.getenv("API_HASH", "")
BOT_TOKEN    = os.getenv("BOT_TOKEN", "")

# ================= DATABASE =====================
MONGO_URI    = os.getenv("MONGO_URI", "")

# ================= OWNER & ACCESS ================
OWNER_ID     = int(os.getenv("OWNER_ID", 0))
CREATOR_NAME = os.getenv("CREATOR_NAME", "Unknown")

# ================= PAYMENT ======================
QRIS_IMAGE      = os.getenv("QRIS_IMAGE", "qr/qris.jpg")      # path gambar QRIS
QR_DANA_IMAGE   = os.getenv("QR_DANA_IMAGE", "qr/dana.jpg")   # path gambar DANA
QR_GOPAY_IMAGE  = os.getenv("QR_GOPAY_IMAGE", "qr/gopay.jpg") # path gambar GOPAY
PAYMENT_TIMEOUT = int(os.getenv("PAYMENT_TIMEOUT", 300))      # 5 menit default

# ================= PREMIUM ======================
PREMIUM_DAYS     = 30
PREMIUM_ROLE     = "PremiumUser"

# ================= LOGGING & BACKUP =============
LOG_GROUP_ID     = int(os.getenv("LOG_GROUP_ID", 0))
BACKUP_CHANNEL   = int(os.getenv("BACKUP_CHANNEL", 0))
BACKUP_INTERVAL  = 3600  # 1 jam

# ================= MESSAGE CONSTANTS =============
MSG_START = f"""
Halo! Saya bot management multi-tenant 🚀
👑 Owner: {CREATOR_NAME}
Ketik /help untuk melihat menu.
"""

MSG_UNAUTHORIZED = "⛔ Anda tidak punya akses untuk perintah ini!"
MSG_PROCESSING   = "⏳ Sedang diproses, mohon tunggu..."
MSG_DONE         = "✅ Berhasil!"
MSG_FAILED       = "❌ Gagal! Coba lagi nanti."

# ================= CHECK VALID CONFIG ============
MISSING = []
if not API_ID     : MISSING.append("API_ID")
if not API_HASH   : MISSING.append("API_HASH")
if not BOT_TOKEN  : MISSING.append("BOT_TOKEN")
if not MONGO_URI  : MISSING.append("MONGO_URI")
if not OWNER_ID   : MISSING.append("OWNER_ID")

if MISSING:
    raise SystemExit(f"\n❗ ERROR: Config berikut belum diisi di .env: {', '.join(MISSING)}\n")

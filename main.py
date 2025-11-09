import os
import sys
import asyncio
import logging
import importlib
import types
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ---------- load environment early ----------
load_dotenv()

# ---------- config ----------
# try config.py, else fallback to env vars
try:
    from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, LOG_CHAT_ID
except Exception:
    API_ID = int(os.getenv("API_ID") or 0)
    API_HASH = os.getenv("API_HASH") or ""
    BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
    MONGO_URI = os.getenv("MONGO_URI") or ""
    try:
        LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0") or 0)
    except:
        LOG_CHAT_ID = 0

if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Missing API_ID/API_HASH/BOT_TOKEN in .env/config. Fix and restart.")
    sys.exit(1)

# ---------- logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ManagementBot")

# ---------- pyrogram client ----------
from pyrogram import Client
try:
    from pyrogram.enums import ParseMode
    DEFAULT_PARSE = ParseMode.HTML
except Exception:
    DEFAULT_PARSE = "html"

app = Client(
    "management_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=DEFAULT_PARSE
)

# ---------- Provide a dynamic utils.helpers bridge module ----------
# This avoids breaking existing handler imports like: from utils.helpers import send_log_all
helpers_mod = types.ModuleType("utils.helpers")
# escape_md_v2 for safety (MarkdownV2) and html escape is intentionally simple:
def escape_md_v2(text: str) -> str:
    if not text:
        return ""
    chars = r"_[]()~`>#+-=|{}.!\\"
    out = "".join("\\"+c if c in chars else c for c in text)
    return out

async def _safe_send_raw(chat_id: int, text: str, as_file_if_long: bool=False, parse_mode=None):
    """internal: tries to send text; if too long or as_file_if_long=True send as file"""
    try:
        if not chat_id:
            return False
        # prefer normal message if short
        if (not as_file_if_long) and len(text) < 4000:
            await app.send_message(chat_id, text, parse_mode=parse_mode)
            return True
        # otherwise upload as file
        import io
        bio = io.BytesIO(text.encode("utf-8"))
        bio.name = "log.txt"
        await app.send_document(chat_id, bio, caption="Log (full)", parse_mode=parse_mode)
        return True
    except Exception as e:
        logger.exception("safe_send_raw failed: %s", e)
        return False

def safe_send_sync(chat_id: int, text: str, as_file_if_long: bool=False, parse_mode=None):
    """Sync wrapper to schedule send in loop"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None
    coro = _safe_send_raw(chat_id, text, as_file_if_long=as_file_if_long, parse_mode=parse_mode)
    if loop and loop.is_running():
        asyncio.create_task(coro)
        return True
    else:
        # try run temporarily
        asyncio.run(coro)
        return True

# Public helpers for handlers:
async def send_log(chat_id: int, text: str, as_file_if_long: bool=False, parse_mode=None):
    return await _safe_send_raw(chat_id, text, as_file_if_long=as_file_if_long, parse_mode=parse_mode)

def send_log_all(text: str, level: str="info"):
    """
    Send log to LOG_CHAT_ID. This strips messages that are marked as [SUBORDER].
    Handlers that want to avoid owner receiving order logs from subowners should prefix
    the message text with '[SUBORDER]'.
    """
    if not LOG_CHAT_ID:
        logger.debug("LOG_CHAT_ID not set — skipping send_log_all.")
        return
    # skip sensitive subowner orders
    if text.startswith("[SUBORDER]"):
        logger.debug("send_log_all: skipped SUBORDER message.")
        return
    # build rich text
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    header = f"[{level.upper()}] {ts}\n"
    full = header + text
    # if long, send as file
    as_file = len(full) > 3000
    safe_send_sync(LOG_CHAT_ID, full, as_file_if_long=as_file, parse_mode=None)

def safe_send(chat_id, text, **kwargs):
    """Compatible API for many handlers that call safe_send"""
    return safe_send_sync(chat_id, text, **kwargs)

# attach to module
helpers_mod.escape_md_v2 = escape_md_v2
helpers_mod.escape_md_v2_alias = escape_md_v2
helpers_mod.safe_send = safe_send
helpers_mod.send_log = send_log
helpers_mod.send_log_all = send_log_all

# register the synthetic module so `import utils.helpers` works
sys.modules["utils.helpers"] = helpers_mod

# ---------- Try load db.mongo (pymongo / motor) ----------
db_module = None
try:
    db_module = importlib.import_module("db.mongo")
    # If db.mongo has init function, call it (some setups expect it)
    if hasattr(db_module, "init_mongo") and callable(getattr(db_module, "init_mongo")):
        try:
            maybe = getattr(db_module, "init_mongo")
            # init_mongo may be sync or coroutine
            if asyncio.iscoroutinefunction(maybe):
                asyncio.get_event_loop().run_until_complete(maybe())
            else:
                maybe()
            logger.info("✅ init_mongo() executed")
        except Exception as e:
            logger.warning("⚠ init_mongo() error: %s", e)
    logger.info("✅ db.mongo loaded")
except ModuleNotFoundError:
    logger.info("ℹ db.mongo not found (continuing without DB)")
except Exception as e:
    logger.exception("🔥 loading db.mongo failed: %s", e)

# ---------- handler loader ----------
def safe_register(name: str, fn):
    try:
        fn(app)
        logger.info("✅ Handler loaded: %s", name)
    except Exception as e:
        logger.exception("🔥 Error loading handler %s: %s", name, e)
        # also notify owner's log (except if SUBORDER concerns)
        try:
            send_log_all(f"Failed to load handler {name}: {e}", level="error")
        except Exception:
            pass

# list of handler names to try (you can add/remove names)
HANDLERS = [
    "start", "help", "menu", "product", "owner", "subowner",
    "payment", "tagall", "premium", "backup", "scheduler", "broadcast"
]

for name in HANDLERS:
    try:
        mod = importlib.import_module(f"handlers.{name}")
        # register function could be register_<name>(app) or register(app)
        register_fn = getattr(mod, f"register_{name}", None) or getattr(mod, "register", None)
        if callable(register_fn):
            safe_register(name, register_fn)
        else:
            logger.info("➡ handlers/%s.py present but no register function", name)
    except ModuleNotFoundError:
        logger.debug("➡ handlers/%s.py not found, skipping", name)
    except Exception as e:
        logger.exception("🔥 Error on handler %s: %s", name, e)

logger.info("✅ Done handler registration attempts.")

# ---------- Daily restart at 00:00 WIB (UTC+7) ----------
async def daily_restart_wib():
    # UTC+7 timezone offset
    tz = timezone(timedelta(hours=7))
    while True:
        now = datetime.now(tz)
        # next midnight WIB
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
        wait = (tomorrow - now).total_seconds()
        logger.info("🔁 Scheduled daily restart at %s WIB (in %.0f seconds)", tomorrow.strftime("%Y-%m-%d %H:%M:%S"), wait)
        await asyncio.sleep(wait)
        try:
            logger.info("🔄 Performing daily restart request (exiting).")
            send_log_all("Daily auto-restart triggered (00:00 WIB)", level="info")
        except Exception:
            pass
        # exit — systemd or process manager should restart the service
        os._exit(0)

# ---------- Start scheduler/backup if available ----------
start_scheduler = None
start_auto_backup = None
try:
    sched = importlib.import_module("utils.scheduler")
    start_scheduler = getattr(sched, "start_scheduler", None)
    logger.info("ℹ utils.scheduler loaded")
except ModuleNotFoundError:
    logger.debug("ℹ no utils.scheduler")
except Exception as e:
    logger.warning("⚠ error loading utils.scheduler: %s", e)

try:
    backup = importlib.import_module("utils.backup")
    start_auto_backup = getattr(backup, "start_auto_backup", None)
    logger.info("ℹ utils.backup loaded")
except ModuleNotFoundError:
    logger.debug("ℹ no utils.backup")
except Exception as e:
    logger.warning("⚠ error loading utils.backup: %s", e)

# ---------- Run coroutine to start bot safely ----------
async def run():
    # start client
    await app.start()
    logger.info("✅ Bot started (Pyrogram).")
    send_log_all("Bot started ✅", level="info")

    # start scheduler/backup if present
    if callable(start_scheduler):
        try:
            start_scheduler()
            logger.info("✅ Scheduler started.")
            send_log_all("Scheduler started", level="info")
        except Exception as e:
            logger.exception("Scheduler start error: %s", e)
            send_log_all(f"Scheduler error: {e}", level="error")

    if callable(start_auto_backup):
        try:
            # if coroutine
            if asyncio.iscoroutinefunction(start_auto_backup):
                asyncio.create_task(start_auto_backup())
            else:
                start_auto_backup()
            logger.info("✅ Auto backup started.")
        except Exception as e:
            logger.exception("Auto backup start error: %s", e)
            send_log_all(f"Auto backup error: {e}", level="error")

    # start daily restart background task
    asyncio.create_task(daily_restart_wib())

    # keep running
    from pyrogram import idle
    await idle()
    await app.stop()
    logger.info("🛑 Bot stopped")

# ---------- entrypoint ----------
if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.exception("🔥 Fatal crash in main: %s", e)
        try:
            send_log_all(f"[CRASH] {e}", level="critical")
        except:
            pass
        raise

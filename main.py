# main.py (REPLACE YOUR FILE WITH THIS)
import logging
import sys
import os
import importlib
from dotenv import load_dotenv

# load .env first (so config.py can read env if it uses os.getenv)
load_dotenv()

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ManagementBot")

# --- config import (try import config.py, fallback to env) ---
try:
    from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI
    logger.info("✅ Loaded config.py")
except Exception as e:
    logger.warning("⚠️ Cannot import config.py cleanly: %s — falling back to env vars", e)
    API_ID = int(os.getenv("API_ID") or 0)
    API_HASH = os.getenv("API_HASH") or ""
    BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
    MONGO_URI = os.getenv("MONGO_URI") or ""

if not API_ID or not API_HASH or not BOT_TOKEN:
    logger.critical("❌ Missing API_ID / API_HASH / BOT_TOKEN in .env or config.py. Fix and re-run.")
    sys.exit(1)

# --- pyrogram client creation ---
from pyrogram import Client
try:
    # prefer using ParseMode enum if available
    from pyrogram.enums import ParseMode
    default_parse_mode = ParseMode.HTML
except Exception:
    default_parse_mode = "html"

app = Client(
    "management_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=default_parse_mode
)

# helper: safe register a handler module's register_xxx function
def safe_register(handler_name: str, register_fn):
    try:
        register_fn(app)
        logger.info("✅ Handler loaded: %s", handler_name)
    except Exception as e:
        logger.exception("🔥 Failed to load handler %s: %s", handler_name, e)

# --- attempt to init mongo module if exists ---
try:
    mod_mongo = importlib.import_module("db.mongo")
    init_mongo = getattr(mod_mongo, "init_mongo", None)
    if callable(init_mongo):
        try:
            init_mongo()  # let init run (should be safe sync init)
            logger.info("✅ init_mongo() executed")
        except Exception as e:
            logger.warning("⚠️ init_mongo() raised: %s", e)
    else:
        logger.info("➡ db.mongo loaded (no init_mongo found)")
except ModuleNotFoundError:
    logger.info("➡ db.mongo not found (skipping mongo init)")
except Exception as e:
    logger.warning("⚠️ error loading db.mongo: %s", e)

# --- load optional utilities (scheduler / backup) if they exist ---
start_scheduler = None
start_auto_backup = None
try:
    mod_sched = importlib.import_module("utils.scheduler")
    start_scheduler = getattr(mod_sched, "start_scheduler", None)
except ModuleNotFoundError:
    logger.debug("utils.scheduler not present (ok).")
except Exception as e:
    logger.warning("error importing utils.scheduler: %s", e)

try:
    mod_backup = importlib.import_module("utils.backup")
    start_auto_backup = getattr(mod_backup, "start_auto_backup", None)
except ModuleNotFoundError:
    logger.debug("utils.backup not present (ok).")
except Exception as e:
    logger.warning("error importing utils.backup: %s", e)

# --- dynamic handler list (edit/add as you implement more handlers) ---
handlers = [
    "start",
    "help",
    "menu",
    "product",
    "owner",
    "subowner",
    "payment",
    "tagall",
    "premium",
    "backup",
    "scheduler"
]

# Try to import each handlers.<name> and call register_<name>(app)
for h in handlers:
    try:
        mod = importlib.import_module(f"handlers.{h}")
        register_fn = None
        # common naming conventions: register_<h> or register_<handlerName>
        register_fn = getattr(mod, f"register_{h}", None) or getattr(mod, "register", None)
        if callable(register_fn):
            safe_register(h, register_fn)
        else:
            logger.info("➡ handlers/%s.py found but no register_%s(app) or register(app) function.", h, h)
    except ModuleNotFoundError:
        logger.debug("➡ handlers/%s.py not found — skipped.", h)
    except Exception as e:
        logger.exception("🔥 Error on handler %s: %s", h, e)

logger.info("✅ Done attempting to load handlers. Starting bot...")

# try start scheduler / backup if available (non-blocking)
try:
    if callable(start_scheduler):
        try:
            start_scheduler()
            logger.info("✅ Scheduler started (utils.scheduler.start_scheduler).")
        except Exception as e:
            logger.warning("⚠️ start_scheduler() raised: %s", e)
    if callable(start_auto_backup):
        try:
            # if it's a coroutine function, try to schedule it with app.loop after start
            # but here we just call; handlers/backup should be defensive
            start_auto_backup()
            logger.info("✅ start_auto_backup() called.")
        except Exception as e:
            logger.warning("⚠️ start_auto_backup() raised: %s", e)
except Exception as e:
    logger.warning("⚠️ Error while attempting to start scheduler/backup: %s", e)

# ===== RUN =====
if __name__ == "__main__":
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually.")
    except Exception as e:
        logger.exception("🔥 Unhandled exception on app.run(): %s", e)
        raise

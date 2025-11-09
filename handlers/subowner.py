from pyrogram import Client, filters from pyrogram.types import ( Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ) import asyncio import logging from datetime import datetime, timedelta

from config import OWNER_ID

Try to import both possible names (partners_col or subowners_col)

from db import mongo as db_mongo

logger = logging.getLogger("handlers.subowner")

choose collection: prefer explicit subowners_col, fallback to partners_col

try: subowners_col = getattr(db_mongo, "subowners_col") except Exception: subowners_col = getattr(db_mongo, "partners_col", None)

helper: detect async/sync collection

def _is_async_col(col): return asyncio.iscoroutinefunction(getattr(col, "find_one", None))

async def _insert_doc(col, doc: dict): if _is_async_col(col) and asyncio.iscoroutinefunction(col.insert_one): res = await col.insert_one(doc) return getattr(res, "inserted_id", None) else: res = col.insert_one(doc) return getattr(res, "inserted_id", None)

async def _find_one(col, *args, **kwargs): if _is_async_col(col): return await col.find_one(*args, **kwargs) else: return col.find_one(*args, **kwargs)

async def _find_many(col, *args, **kwargs): if _is_async_col(col): cursor = col.find(*args, **kwargs) return [d async for d in cursor] else: return list(col.find(*args, **kwargs))

async def _update_one(col, filter_q, update_q, upsert=False): if _is_async_col(col) and asyncio.iscoroutinefunction(col.update_one): return await col.update_one(filter_q, update_q, upsert=upsert) else: return col.update_one(filter_q, update_q, upsert=upsert)

async def _delete_one(col, filter_q): if _is_async_col(col) and asyncio.iscoroutinefunction(col.delete_one): return await col.delete_one(filter_q) else: return col.delete_one(filter_q)

In-memory pending flows per user (subowner setup / settings flows)

PENDING = {}  # {user_id: {"flow":"create"|"settings", "step":int, "data":{}}}

DEFAULT_PREMIUM_DAYS = 30 MAX_SUBOWNERS = 5  # optional guard (owner asked max 5)

def _owner_keyboard(): return InlineKeyboardMarkup([ [InlineKeyboardButton("➕ Add Subowner", callback_data="sub:owner:add")], [InlineKeyboardButton("📋 List Subowners", callback_data="sub:owner:list")], ])

def _subowner_kb(): return InlineKeyboardMarkup([ [InlineKeyboardButton("⚙️ Settings Store", callback_data="sub:settings")], [InlineKeyboardButton("📄 Info Akun", callback_data="sub:info")], ])

def register_subowner(app: Client): """Register subowner-related handlers. Call this with the pyrogram Client instance."""

@app.on_message(filters.command("addsub") & filters.user(OWNER_ID) & filters.private)
async def cmd_addsub_owner(client: Client, message: Message):
    """
    Owner command to create a subowner record quickly.
    Usage: /addsub <BOT_TOKEN> <LOG_GROUP_ID> <MAIN_GROUP_ID> <STORE_NAME>
    """
    try:
        parts = message.text.split(maxsplit=4)
        if len(parts) < 5:
            return await message.reply("Usage: /addsub <BOT_TOKEN> <LOG_GROUP_ID> <MAIN_GROUP_ID> <STORE_NAME>")

        _, bot_token, log_group_raw, main_group_raw, store_name = parts
        try:
            log_group = int(log_group_raw)
            main_group = int(main_group_raw)
        except Exception:
            return await message.reply("LOG_GROUP_ID and MAIN_GROUP_ID harus berupa angka (contoh -100123456789)")

        # optional: guard max subowners
        try:
            current = await _find_many(subowners_col, {})
            if isinstance(current, list) and len(current) >= MAX_SUBOWNERS:
                return await message.reply(f"⚠️ Maksimal subowner = {MAX_SUBOWNERS}. Hapus dulu jika ingin tambah.")
        except Exception:
            # ignore if collection not available
            pass

        doc = {
            "bot_token": bot_token,
            "log_group": log_group,
            "main_group": main_group,
            "store": store_name,
            "owner_id": message.from_user.id,
            "created_at": datetime.utcnow(),
            "premium_until": (datetime.utcnow() + timedelta(days=DEFAULT_PREMIUM_DAYS)).isoformat(),
            "active": True,
        }

        inserted_id = await _insert_doc(subowners_col, doc)
        await message.reply(f"✅ Subowner dibuat: `{inserted_id}`\nStore: {store_name}\nLog: {log_group}", parse_mode="markdown")

    except Exception as e:
        logger.exception("cmd_addsub_owner error: %s", e)
        await message.reply(f"❌ Error: {e}")

@app.on_callback_query(filters.regex(r"^sub:owner:"))
async def owner_sub_cb(client: Client, callback: CallbackQuery):
    # owner menu actions
    action = callback.data.split(":", 2)[2]
    if action == "add":
        await callback.message.edit_text(
            "📌 Gunakan perintah:\n/addsub <BOT_TOKEN> <LOG_GROUP_ID> <MAIN_GROUP_ID> <STORE_NAME>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="menu_owner")]])
        )
        await callback.answer()

    elif action == "list":
        try:
            rows = await _find_many(subowners_col, {})
            if not rows:
                await callback.message.edit_text("⚠️ Belum ada subowner tersimpan.")
                await callback.answer()
                return

            text = "<b>📋 Subowners</b>\n\n"
            for r in rows:
                sid = getattr(r, "_id", r.get("_id"))
                text += f"`{sid}` — {r.get('store')} — log:{r.get('log_group')} — active:{r.get('active')}\n"

            await callback.message.edit_text(text, parse_mode="html")
            await callback.answer()
        except Exception as e:
            logger.exception("owner_sub_cb list error: %s", e)
            await callback.answer("Gagal memuat list", show_alert=True)

    else:
        await callback.answer()

# -------------------- subowner flow: they register via /start or via a special command --------------------
@app.on_message(filters.command("become") & filters.private)
async def cmd_become_subowner(client: Client, message: Message):
    """
    Optional: allow users to request becoming a subowner (owner still must approve manually via /addsub)
    Usage: /become <store name>
    """
    await message.reply("🔒 Untuk menjadi subowner, pemilik harus menambahkan via /addsub. Hubungi owner.")

# -------------------- subowner settings menu --------------------
@app.on_callback_query(filters.regex(r"^sub:settings$"))
async def sub_settings_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    # fetch subowner doc by owner mapping - subowners store their owner_id (the owner who created them)
    try:
        doc = await _find_one(subowners_col, {"owner_id": user_id})
    except Exception:
        doc = None

    if not doc:
        # If not found by owner_id, allow lookup by user id stored (some flows store subowner user id)
        await callback.answer("⚠️ Anda tidak terdaftar sebagai subowner di sistem.", show_alert=True)
        return

    text = (
        f"⚙️ Pengaturan Store — <b>{doc.get('store')}</b>\n\n"
        "Pilih setting yang ingin diubah:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏷 Ubah Nama Store", callback_data="sub:set:name")],
        [InlineKeyboardButton("🏧 Ubah Info Pembayaran", callback_data="sub:set:payment")],
        [InlineKeyboardButton("🔁 Set Grup Log", callback_data="sub:set:log")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_start")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="html")
    except Exception:
        pass
    await callback.answer()

# individual subowner settings handlers (start flows)
@app.on_callback_query(filters.regex(r"^sub:set:"))
async def sub_settings_flow_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    key = callback.data.split(":", 2)[2]
    if key not in ("name", "payment", "log"):
        await callback.answer(); return

    PENDING[user_id] = {"flow": "settings", "step": 1, "type": key, "data": {}}
    if key == "name":
        await callback.message.edit_text("✏️ Kirim nama store baru (satu pesan):")
    elif key == "payment":
        await callback.message.edit_text("💳 Kirim instruksi pembayaran baru (contoh: DANA:0812xxxx / BCA:123xxxx):")
    elif key == "log":
        await callback.message.edit_text("🔗 Kirim ID grup log (contoh: -100123456789):")
    await callback.answer()

# handler that receives messages for pending flows (create subowner via interactive owner? settings for subowner)
@app.on_message(filters.private & ~filters.command(["start", "help"]))
async def pending_sub_flow_msg(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in PENDING:
        return
    state = PENDING.pop(user_id)
    try:
        if state.get("flow") == "settings":
            key = state.get("type")
            value = message.text.strip()
            # find the subowner doc corresponding to this user
            doc = await _find_one(subowners_col, {"owner_id": user_id})
            if not doc:
                return await message.reply("⚠️ Data subowner tidak ditemukan.")

            if key == "name":
                await _update_one(subowners_col, {"_id": doc.get("_id")}, {"$set": {"store": value}})
                await message.reply("✅ Nama store diperbarui.")
            elif key == "payment":
                await _update_one(subowners_col, {"_id": doc.get("_id")}, {"$set": {"payment_info": value}})
                await message.reply("✅ Instruksi pembayaran diperbarui.")
            elif key == "log":
                try:
                    gid = int(value)
                except Exception:
                    return await message.reply("⚠️ Format ID grup salah. Harus angka (contoh -100123456789)")
                await _update_one(subowners_col, {"_id": doc.get("_id")}, {"$set": {"log_group": gid}})
                await message.reply("✅ Grup log diperbarui.")
    except Exception as e:
        logger.exception("pending_sub_flow_msg error: %s", e)
        await message.reply(f"❌ Terjadi error: {e}")

# --------- subowner info panel ---------
@app.on_callback_query(filters.regex(r"^sub:info$"))
async def sub_info_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    doc = await _find_one(subowners_col, {"owner_id": user_id})
    if not doc:
        return await callback.answer("⚠️ Anda tidak terdaftar sebagai subowner.", show_alert=True)

    text = (
        f"<b>ℹ️ Info Subowner</b>\n\n"
        f"Store: {doc.get('store')}\n"
        f"Log Group: {doc.get('log_group')}\n"
        f"Main Group: {doc.get('main_group')}\n"
        f"Premium Until: {doc.get('premium_until')}\n"
        f"Active: {doc.get('active')}"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Settings", callback_data="sub:settings")]])
    try:
        await callback.message.edit_text(text, parse_mode="html", reply_markup=kb)
    except Exception:
        pass
    await callback.answer()

logger.info("✅ handlers/subowner.py registered")

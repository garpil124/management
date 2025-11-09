
    import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import OWNER_ID
from db.mongo import partners_col, users_col

# --------------------------------------
# STATE ADD PARTNER
PENDING_PARTNER = {}

# --------------------------------------
# Helper DB (support async/sync pymongo)
async def _insert_doc(col, doc):
    if asyncio.iscoroutinefunction(getattr(col, "insert_one", None)):
        r = await col.insert_one(doc)
        return str(r.inserted_id)
    r = col.insert_one(doc)
    return str(r.inserted_id)

async def _find_docs(col, q=None):
    q = q or {}
    if asyncio.iscoroutinefunction(getattr(col, "find", None)):
        return await col.find(q).to_list(None)
    return list(col.find(q))

async def _delete_doc(col, q):
    if asyncio.iscoroutinefunction(getattr(col, "delete_one", None)):
        return await col.delete_one(q)
    return col.delete_one(q)

# --------------------------------------
# MENU OWNER
@Client.on_callback_query(filters.regex("^owner_menu$") & filters.user(OWNER_ID))
async def owner_menu_cb(c: Client, q: CallbackQuery):
    kb = [
        [InlineKeyboardButton("➕ Tambah Partner", "addpartner_start")],
        [InlineKeyboardButton("📜 Daftar Partner", "list_partner")],
        [InlineKeyboardButton("📣 Broadcast", "owner_broadcast")],
        [InlineKeyboardButton("🛍 Owner Store", "owner_store")],
        [InlineKeyboardButton("⚙️ Setting", "owner_setting")]
    ]
    await q.message.edit_text(
        "👑 *Owner Panel*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="markdown"
    )
    await q.answer()

# --------------------------------------
# ADD PARTNER (STEP 1)
@Client.on_callback_query(filters.regex("^addpartner_start$") & filters.user(OWNER_ID))
async def addpartner_start(c, q):
    uid = q.from_user.id
    PENDING_PARTNER[uid] = {"step": "token", "data": {}}
    await q.message.edit_text(
        "🆕 *Add Partner*\n\nKirim Bot Token partner\nContoh:\n`123456:ABCXYZ`",
        parse_mode="markdown"
    )
    await q.answer()

@Client.on_message(filters.command("cancel") & filters.user(OWNER_ID))
async def cancel_partner(c, m):
    if m.from_user.id in PENDING_PARTNER:
        PENDING_PARTNER.pop(m.from_user.id)
        await m.reply("✅ Proses dibatalkan")
    else:
        await m.reply("⚠ Tidak ada proses berjalan")

@Client.on_message(filters.user(OWNER_ID) & filters.private)
async def partner_flow(c, m):
    uid = m.from_user.id
    if uid not in PENDING_PARTNER:
        return

    flow = PENDING_PARTNER[uid]
    text = m.text.strip()

    if flow["step"] == "token":
        flow["data"]["token"] = text
        flow["step"] = "log"
        return await m.reply("Kirim ID Group Log (-100xxxx)")

    if flow["step"] == "log":
        if not text.lstrip("-").isdigit():
            return await m.reply("❌ Harus angka!")
        flow["data"]["log"] = int(text)
        flow["step"] = "main"
        return await m.reply("Kirim ID Group Utama (-100xxx)")

    if flow["step"] == "main":
        if not text.lstrip("-").isdigit():
            return await m.reply("❌ Harus angka!")
        flow["data"]["main"] = int(text)
        flow["step"] = "store"
        return await m.reply("Kirim Nama Store Partner")

    if flow["step"] == "store":
        d = flow["data"]
        d["store"] = text
        d["expired"] = datetime.utcnow() + timedelta(days=30)
        d["created"] = datetime.utcnow()

        await _insert_doc(partners_col, d)
        PENDING_PARTNER.pop(uid)

        await m.reply("✅ Partner berhasil ditambahkan!")

# --------------------------------------
# LIST PARTNER
@Client.on_callback_query(filters.regex("^list_partner$") & filters.user(OWNER_ID))
async def list_partner(c, q):
    data = await _find_docs(partners_col)
    if not data:
        return await q.message.edit_text("❗ Belum ada partner")

    msg = "📜 *Daftar Partner:*\n\n"
    for x in data:
        msg += f"🏪 {x.get('store')}\n"
        msg += f"📡 Token: `{x.get('token')[:10]}...`\n"
        msg += f"⏳ Expired: `{x.get('expired')}`\n"
        msg += f"🧾 Log: `{x.get('log')}`\n"
        msg += "━━━━━━━━━━━\n"

    await q.message.edit_text(msg, parse_mode="markdown")
    await q.answer()

# --------------------------------------
# BROADCAST
@Client.on_callback_query(filters.regex("^owner_broadcast$") & filters.user(OWNER_ID))
async def ask_bc(c, q):
    await q.message.edit_text("📣 Kirim pesan untuk broadcast ke semua user")
    PENDING_PARTNER[q.from_user.id] = {"step": "broadcast"}
    await q.answer()

@Client.on_message(filters.user(OWNER_ID) & filters.private)
async def run_bc(c, m):
    uid = m.from_user.id
    if uid not in PENDING_PARTNER:
        return

    if PENDING_PARTNER[uid].get("step") == "broadcast":
        PENDING_PARTNER.pop(uid)
        users = await _find_docs(users_col)
        sent, fail = 0, 0

        for u in users:
            try:
                await c.send_message(u["user_id"], m.text)
                sent+=1
            except:
                fail+=1

        await m.reply(f"✅ Broadcast selesai\n✔ Terkirim: {sent}\n❌ Gagal: {fail}")

# --------------------------------------
# OWNER STORE (template)
@Client.on_callback_query(filters.regex("^owner_store$") & filters.user(OWNER_ID))
async def owner_store(c, q):
    await q.message.edit_text("🛍 Menu Owner Store (coming soon)")
    await q.answer()

# --------------------------------------
# SETTING
@Client.on_callback_query(filters.regex("^owner_setting$") & filters.user(OWNER_ID))
async def owner_setting(c, q):
    await q.message.edit_text("⚙ Setting Owner (coming soon)")
    await q.answer()

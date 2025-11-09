import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup
)

from config import OWNER_ID
from db.mongo import partners_col, users_col  # pastikan sudah benar

# --------------------------------------
# State add-partner interaktif
PENDING_PARTNER = {}

# --------------------------------------
# Helper DB compatible async/sync
async def _insert_doc(col, doc):
    if asyncio.iscoroutinefunction(getattr(col, "insert_one", None)):
        res = await col.insert_one(doc)
        return str(res.inserted_id)
    res = col.insert_one(doc)
    return str(res.inserted_id)

async def _find_docs(col, query=None):
    query = query or {}
    if asyncio.iscoroutinefunction(getattr(col, "find", None)):
        return await col.find(query).to_list(None)
    return list(col.find(query))

async def _delete_doc(col, query):
    if asyncio.iscoroutinefunction(getattr(col, "delete_one", None)):
        return await col.delete_one(query)
    return col.delete_one(query)

# --------------------------------------
# MENU UTAMA OWNER
@Client.on_callback_query(filters.regex("^owner_menu$") & filters.user(OWNER_ID))
async def owner_menu_cb(c: Client, q: CallbackQuery):
    kb = [
        [InlineKeyboardButton("➕ Tambah Partner", "addpartner_start")],
        [InlineKeyboardButton("📜 Daftar Partner", "list_partners")],
        [InlineKeyboardButton("📣 Broadcast", "broadcast_all")],
        [InlineKeyboardButton("🛍️ Jualan Bot Owner", "owner_store")],
        [InlineKeyboardButton("⚙️ Pengaturan", "owner_setting")]
    ]
    await q.message.edit_text(
        "👑 **Menu Owner (Full Akses)**",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="markdown"
    )
    await q.answer()

# --------------------------------------
# START ADD PARTNER (INTERAKTIF)
@Client.on_callback_query(filters.regex("^addpartner_start$") & filters.user(OWNER_ID))
async def start_add_partner_cb(c: Client, q: CallbackQuery):
    uid = q.from_user.id
    PENDING_PARTNER[uid] = {"step": "token", "data": {}}
    await q.message.edit_text(
        "🆕 *Tambah Partner (Step 1/4)*\n\n"
        "Silakan kirim **Bot Token** partner.\n"
        "Contoh: `123456:ABC-abc123`\n\n"
        "Ketik /cancel untuk batal.",
        parse_mode="markdown"
    )
    await q.answer()

@Client.on_message(filters.command("cancel") & filters.user(OWNER_ID) & filters.private)
async def cancel_add_partner(c: Client, m: Message):
    if m.from_user.id in PENDING_PARTNER:
        PENDING_PARTNER.pop(m.from_user.id)
        return await m.reply("❌ Proses dibatalkan.")
    await m.reply("⚠️ Tidak ada proses yang berjalan.")

@Client.on_message(filters.private & filters.user(OWNER_ID))
async def partner_flow_handler(c: Client, m: Message):
    uid = m.from_user.id
    if uid not in PENDING_PARTNER:
        return

    flow = PENDING_PARTNER[uid]
    txt = (m.text or "").strip()

    # 1. Token
    if flow["step"] == "token":
        flow["data"]["token"] = txt
        flow["step"] = "log"
        return await m.reply("✅ Token diterima.\nKirim **Group Log ID** (contoh: -10012345678)")

    # 2. Log group
    if flow["step"] == "log":
        if not txt.lstrip("-").isdigit():
            return await m.reply("⚠️ Format salah, harus ID angka.")
        flow["data"]["log"] = int(txt)
        flow["step"] = "main"
        return await m.reply("✅ Log ID diterima.\nKirim **Group Utama ID** bot partner.")

    # 3. Main group
    if flow["step"] == "main":
        if not txt.lstrip("-").isdigit():
            return await m.reply("⚠️ Format salah, harus ID angka.")
        flow["data"]["main"] = int(txt)
        flow["step"] = "store"
        return await m.reply("✅ Group utama diterima.\nKirim **Nama Store** partner.")

    # 4. Store name
    if flow["step"] == "store":
        flow["data"]["store"] = txt
        flow["step"] = "confirm"

        d = flow["data"]
        exp = datetime.utcnow() + timedelta(days=30)
        flow["data"]["expired"] = exp

        text = (
            "📌 **Konfirmasi Data Partner**\n\n"
            f"🤖 Token: `{d['token'][:10]}...`\n"
            f"📌 Log Group: `{d['log']}`\n"
            f"📍 Main Group: `{d['main']}`\n"
            f"🛍️ Store: *{d['store']}*\n"
            f"⏳ Aktif hingga: `{exp.strftime('%Y-%m-%d')}`\n\n"
            "Pilih aksi:"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Simpan", "partner_confirm")],
            [InlineKeyboardButton("❌ Batal", "partner_cancel")]
        ])
        return await m.reply(text, reply_markup=kb, parse_mode="markdown")

@Client.on_callback_query(filters.regex("^partner_confirm$") & filters.user(OWNER_ID))
async def save_partner(c: Client, q: CallbackQuery):
    uid = q.from_user.id
    data = PENDING_PARTNER[uid]["data"]
    PENDING_PARTNER.pop(uid)

    doc = {
        "token": data["token"],
        "log_group": data["log"],
        "main_group": data["main"],
        "store": data["store"],
        "owner_id": uid,
        "expired": data["expired"],
        "created_at": datetime.utcnow(),
        "active": True,
        "products": []
    }

    pid = await _insert_doc(partners_col, doc)
    await q.message.edit_text(f"✅ Partner berhasil dibuat!\n🆔 ID: `{pid}`", parse_mode="markdown")
    await q.answer()

@Client.on_callback_query(filters.regex("^partner_cancel$") & filters.user(OWNER_ID))
async def cancel_partner_cb(c: Client, q: CallbackQuery):
    PENDING_PARTNER.pop(q.from_user.id, None)
    await q.message.edit_text("❌ Pembuatan partner dibatalkan.")
    await q.answer()

# --------------------------------------
# LIST PARTNER
@Client.on_callback_query(filters.regex("^list_partners$") & filters.user(OWNER_ID))
async def list_partners(c: Client, q: CallbackQuery):
    partners = await _find_docs(partners_col)
    if not partners:
        return await q.answer("Belum ada partner", show_alert=True)

    text = "📋 **Daftar Partner**\n\n"
    kb = []

    for p in partners:
        exp = p.get("expired")
        status = "✅ Aktif" if exp and exp > datetime.utcnow() else "⛔ Expired"
        text += f"• {p['store']} — {status}\n"
        kb.append([InlineKeyboardButton(p["store"], f"partner:{p['_id']}")])

    kb.append([InlineKeyboardButton("🔙 Kembali", "owner_menu")])

    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="markdown")
    await q.answer()

# --------------------------------------
# DETAIL // HAPUS PARTNER
@Client.on_callback_query(filters.regex(r"^partner:(.*)") & filters.user(OWNER_ID))
async def detail_partner(c: Client, q: CallbackQuery):
    pid = q.data.split(":", 1)[1]
    partners = await _find_docs(partners_col, {"_id": pid})
    if not partners:
        return await q.answer("Partner tidak ditemukan", True)

    p = partners[0]
    exp = p.get("expired")
    exp_t = exp.strftime("%Y-%m-%d") if exp else "?"
    status = "✅ Aktif" if exp and exp > datetime.utcnow() else "⛔ Expired"
    text = (
        f"🛍️ *{p['store']}*\n"
        f"🆔 ID: `{pid}`\n"
        f"⏳ Expired: `{exp_t}` ({status})\n"
        f"👥 Main Group: `{p.get('main_group')}`\n"
        f"📌 Log Group: `{p.get('log_group')}`"
    )
    kb = [
        [InlineKeyboardButton("🗑️ Hapus Partner", f"delpartner:{pid}")],
        [InlineKeyboardButton("🔙 Kembali", "list_partners")]
    ]
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="markdown")
    await q.answer()

@Client.on_callback_query(filters.regex(r"^delpartner:(.*)") & filters.user(OWNER_ID))
async def delete_partner(c: Client, q: CallbackQuery):
    pid = q.data.split(":", 1)[1]
    await _delete_doc(partners_col, {"_id": pid})
    await q.message.edit_text("✅ Partner berhasil dihapus.")
    await q.answer()

# --------------------------------------
# BROADCAST KE SEMUA USER & PARTNER
@Client.on_callback_query(filters.regex("^broadcast_all$") & filters.user(OWNER_ID))
async def broadcast_start(c: Client, q: CallbackQuery):
    await q.message.edit_text("📣 Kirim pesan yang mau di broadcast ke SEMUA USER + PARTNER")
    await q.answer()
    PENDING_PARTNER[q.from_user.id] = {"step": "broadcast"}

@Client.on_message(filters.private & filters.user(OWNER_ID))
async def broadcast_handler(c: Client, m: Message):
    uid = m.from_user.id
    if uid not in PENDING_PARTNER or PENDING_PARTNER[uid].get("step") != "broadcast":
        return

    users = await _find_docs(users_col)
    partners = await _find_docs(partners_col)
    targets = [u["user_id"] for u in users if "user_id" in u]
    targets += [p["main_group"] for p in partners if "main_group" in p]

    done = 0
    for tid in targets:
        try:
            await c.copy_message(chat_id=tid, from_chat_id=m.chat.id, message_id=m.id)
            done += 1
        except:
            pass

    PENDING_PARTNER.pop(uid)
    await m.reply(f"✅ Broadcast selesai terkirim ke {done} target.")

# --------------------------------------
# MENU STORE OWNER (OWNER JUALAN JUGA)
@Client.on_callback_query(filters.regex("^owner_store$") & filters.user(OWNER_ID))
async def owner_store_menu(c: Client, q: CallbackQuery):
    kb = [
        [InlineKeyboardButton("➕ Tambah Produk", "owner_addprod")],
        [InlineKeyboardButton("📦 Daftar Produk", "owner_listprod")],
        [InlineKeyboardButton("🔙 Kembali", "owner_menu")]
    ]
    await q.message.edit_text("🛍️ **Toko Bot Owner**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="markdown")
    await q.answer()

# --------------------------------------
# SETTING OWNER (placeholder)
@Client.on_callback_query(filters.regex("^owner_setting$") & filters.user(OWNER_ID))
async def owner_setting(c: Client, q: CallbackQuery):
    kb = [[InlineKeyboardButton("🔙 Kembali", "owner_menu")]]
    await q.message.edit_text("⚙️ Pengaturan Owner\n(akan dikembangkan..)", reply_markup=InlineKeyboardMarkup(kb))
    await q.answer()

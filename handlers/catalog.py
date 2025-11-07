# handlers/catalog.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from db.mongo import products_col, partners_col
from bson.objectid import ObjectId

PAGE_SIZE = 6

@Client.on_message(filters.command(["catalog","produk"]))
async def show_catalog(client: Client, message: Message):
    page = 0
    await _send_catalog_page(client, message.chat.id, page)

async def _send_catalog_page(client, chat_id, page=0, owner_id=None):
    skip = page * PAGE_SIZE
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
    cursor = products_col.find(query).skip(skip).limit(PAGE_SIZE)
    items = []
    async for p in cursor:
        items.append(p)

    if not items:
        return await client.send_message(chat_id, "📦 Katalog kosong.")

    text_lines = []
    kb = []
    for p in items:
        pid = str(p["_id"])
        text_lines.append(f"• <b>{p['name']}</b>\n  Rp{p['price']}\n")
        kb.append([InlineKeyboardButton(f"{p['name']} — Rp{p['price']}", callback_data=f"prod:{pid}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"cat:None:{page-1}"))
    nav.append(InlineKeyboardButton("Next ⏭️", callback_data=f"cat:None:{page+1}"))
    kb.append(nav)
    kb.append([InlineKeyboardButton("🏪 Kembali", callback_data="menu")])

    await client.send_message(chat_id, "\n".join(text_lines), reply_markup=InlineKeyboardMarkup(kb), parse_mode="html")

@Client.on_callback_query(filters.regex(r"^cat:"))
async def on_cat_page(client: Client, cq: CallbackQuery):
    _, owner_s, page_s = cq.data.split(":")
    owner_id = None if owner_s in ("None","0","") else int(owner_s)
    page = int(page_s)
    await _send_catalog_page(client, cq.message.chat.id, page, owner_id)
    await cq.answer()

@Client.on_callback_query(filters.regex(r"^prod:"))
async def on_prod(client: Client, cq: CallbackQuery):
    pid = cq.data.split(":",1)[1]
    try:
        doc = await products_col.find_one({"_id": ObjectId(pid)})
    except:
        await cq.answer("Produk tidak ditemukan", show_alert=True)
        return
    if not doc:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)

    text = f"<b>{doc['name']}</b>\n\n{doc.get('desc','-')}\n\nHarga: Rp{doc['price']}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Beli Sekarang", callback_data=f"buy:{pid}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="cat:None:0")]
    ])
    await cq.message.edit(text, reply_markup=kb, parse_mode="html")
    await cq.answer()

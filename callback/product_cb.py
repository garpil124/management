# management/callback/product_cb.py

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import asyncio
import html
import logging
from datetime import datetime

from db.mongo import products_col  # collection produk
from config import OWNER_ID        # optional untuk akses owner

logger = logging.getLogger("product_callback")

# In-memory cache untuk proses add/edit
PENDING = {}

def esc_html(text: str) -> str:
    return html.escape(str(text)) if text else ""

def is_async_col(col):
    return asyncio.iscoroutinefunction(getattr(col, "find_one", None))

def product_action_buttons(prod: dict, is_owner: bool):
    buttons = [
        [InlineKeyboardButton("💳 Bayar / Konfirmasi", callback_data=f"pay_{prod['code']}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_product")]
    ]
    if is_owner:
        buttons.insert(0, [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_product:{prod['code']}"),
            InlineKeyboardButton("🗑️ Hapus", callback_data=f"delete_product:{prod['code']}")
        ])
    return InlineKeyboardMarkup(buttons)


def register_callback_handlers(app: Client):

    # /produk -> tampilkan daftar
    @app.on_message(filters.command("produk") & filters.private)
    async def cmd_produk(client: Client, message: Message):
        user_id = message.from_user.id

        try:
            if is_async_col(products_col):
                cursor = products_col.find({"owner_id": user_id}).sort("created_at", -1)
                data = [p async for p in cursor]
            else:
                data = list(products_col.find({"owner_id": user_id}).sort("created_at", -1).limit(50))
        except Exception as e:
            logger.exception(e)
            return await message.reply("⚠️ Error saat load produk.")

        if not data:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]])
            return await message.reply("📦 Belum ada produk.", reply_markup=kb)

        text = "<b>📦 Produkmu:</b>\n\n"
        for p in data[:10]:
            text += f"• <b>{esc_html(p['name'])}</b> — Rp{esc_html(p['price'])} (<code>{p['code']}</code>)\n"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")],
            [InlineKeyboardButton("📄 Lihat Semua", callback_data="menu_product")]
        ])
        await message.reply(text, parse_mode="html", reply_markup=kb)

    # LIST produk + tombol pilihan
    @app.on_callback_query(filters.regex("^menu_product$"))
    async def cb_menu_product(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id

        try:
            if is_async_col(products_col):
                cursor = products_col.find({"owner_id": user_id})
                data = [p async for p in cursor]
            else:
                data = list(products_col.find({"owner_id": user_id}).limit(100))
        except Exception as e:
            logger.exception(e)
            return await callback.answer("Error ambil produk", show_alert=True)

        if not data:
            return await callback.message.edit_text(
                "📦 Belum ada produk.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]])
            )

        buttons = []
        for p in data[:25]:
            buttons.append([InlineKeyboardButton(f"{p['name']} — Rp{p['price']}", callback_data=f"product_{p['code']}")])

        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")])

        await callback.message.edit_text(
            "<b>📦 Pilih Produk:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="html"
        )

    # Detail produk
    @app.on_callback_query(filters.regex(r"^product_"))
    async def cb_show_product(client: Client, callback: CallbackQuery):
        code = callback.data.split("_")[1]
        user_id = callback.from_user.id

        try:
            prod = await products_col.find_one({"code": code, "owner_id": user_id}) \
                if is_async_col(products_col) else \
                products_col.find_one({"code": code, "owner_id": user_id})
        except Exception as e:
            logger.exception(e)
            return await callback.answer("Error load produk", show_alert=True)

        if not prod:
            return await callback.answer("Produk tidak ditemukan", show_alert=True)

        text = (
            "<b>🧾 Detail Produk</b>\n\n"
            f"📌 <b>{esc_html(prod['name'])}</b>\n"
            f"💳 Harga: Rp{esc_html(prod['price'])}\n"
            f"🆔 Code: <code>{esc_html(prod['code'])}</code>\n\n"
            f"{esc_html(prod.get('desc','-'))}"
        )

        await callback.message.edit_text(
            text,
            parse_mode="html",
            reply_markup=product_action_buttons(prod, prod["owner_id"] == user_id)
        )

    # Tambah produk
    @app.on_callback_query(filters.regex("^add_product$"))
    async def cb_add_product(client: Client, callback: CallbackQuery):
        PENDING[callback.from_user.id] = {"action": "add", "code": None}
        await callback.message.edit_text(
            "🆕 <b>Tambah Produk</b>\n\n"
            "Format:\n"
            "<code>Nama | Harga | KODE | Deskripsi</code>"
            "\n\n/cancel untuk batal.",
            parse_mode="html"
        )

    # Edit produk
    @app.on_callback_query(filters.regex(r"^edit_product:"))
    async def cb_edit_product(client: Client, callback: CallbackQuery):
        user = callback.from_user.id
        code = callback.data.split(":")[1]

        PENDING[user] = {"action": "edit", "code": code}
        await callback.message.edit_text(
            "✏️ <b>Edit Produk</b>\n\n"
            "Format:\n"
            "<code>Nama | Harga | KODE | Deskripsi</code>"
            "\n\n/cancel untuk batal.",
            parse_mode="html"
        )

    # Hapus produk
    @app.on_callback_query(filters.regex(r"^delete_product:"))
    async def cb_delete_product(client: Client, callback: CallbackQuery):
        user = callback.from_user.id
        code = callback.data.split(":")[1]

        await (products_col.delete_one({"code": code, "owner_id": user})
               if not is_async_col(products_col)
               else products_col.delete_one({"code": code, "owner_id": user}))

        await callback.message.edit_text("✅ Produk dihapus.")
        await callback.answer("Dihapus.")

    # Handler data saat user kirim text
    @app.on_message(filters.private & ~filters.command(["start", "help", "produk"]))
    async def pending_msg(client: Client, message: Message):
        user = message.from_user.id
        if user not in PENDING:
            return

        state = PENDING.pop(user)
        action = state["action"]
        code_expected = state.get("code")
        text = message.text or ""

        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 3:
            return await message.reply("❌ Format salah.\nGunakan:\n`Nama | Harga | Code | Deskripsi (optional)`")

        name, price, code = parts[:3]
        desc = parts[3] if len(parts) > 3 else ""

        doc = {
            "name": name,
            "price": price,
            "code": code,
            "desc": desc,
            "owner_id": user,
            "created_at": datetime.utcnow(),
        }

        if action == "add":
            exists = await products_col.find_one({"code": code, "owner_id": user}) \
                if is_async_col(products_col) else \
                products_col.find_one({"code": code, "owner_id": user})

            if exists:
                return await message.reply("⚠️ Kode produk sudah ada.")

            await (products_col.insert_one(doc)
                   if not is_async_col(products_col)
                   else products_col.insert_one(doc))

            await message.reply(f"✅ Produk ditambahkan:\n<b>{esc_html(name)}</b>", parse_mode="html")

        elif action == "edit":
            await (products_col.update_one({"code": code_expected, "owner_id": user}, {"$set": doc})
                   if not is_async_col(products_col)
                   else products_col.update_one({"code": code_expected, "owner_id": user}, {"$set": doc}))

            await message.reply(f"✅ Produk diperbarui: <b>{esc_html(name)}</b>", parse_mode="html")

    # Cancel flow
    @app.on_message(filters.command("cancel") & filters.private)
    async def cancel(client, message):
        PENDING.pop(message.from_user.id, None)
        await message.reply("🔴 Dibatalin.")

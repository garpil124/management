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

from config import OWNER_ID  # make sure this exists
from db.mongo import products_col  # ensure this is exported by db/mongo.py

logger = logging.getLogger("product")

# in-memory pending states: { user_id: {"action": "add"|"edit", "code": code_or_None} }
PENDING = {}

# helper: escape for HTML
def esc_html(text: str) -> str:
    if not text:
        return ""
    return html.escape(str(text))

# helper: detect if collection methods are coroutine (motor) or sync (pymongo)
def is_async_col(col):
    return asyncio.iscoroutinefunction(getattr(col, "find_one", None))

# helper: build product buttons for owner/user actions
def product_action_buttons(prod: dict, is_owner_of_prod: bool):
    buttons = [
        [InlineKeyboardButton("💳 Bayar / Konfirmasi", callback_data=f"pay_{prod['code']}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_product")]
    ]
    if is_owner_of_prod:
        buttons.insert(0, [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_product:{prod['code']}"),
            InlineKeyboardButton("🗑️ Hapus", callback_data=f"delete_product:{prod['code']}")
        ])
    return InlineKeyboardMarkup(buttons)

# register function
def register_product(app: Client):

    # ---------- /produk command (manual)
    @app.on_message(filters.command("produk") & filters.private)
    async def cmd_produk(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else 0
        # fetch products for this owner (per-owner)
        query = {"owner_id": user_id}
        try:
            if is_async_col(products_col):
                cursor = products_col.find(query).sort("created_at", -1)
                data = [p async for p in cursor]
            else:
                data = list(products_col.find(query).sort("created_at", -1).limit(100))
        except Exception as e:
            logger.exception("Failed to load products: %s", e)
            return await message.reply("⚠️ Gagal memuat produk. Cek log.")

        if not data:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]])
            return await message.reply("📦 Belum ada produk. Gunakan tombol tambah untuk menambah.", reply_markup=kb)

        # show first page (10 items)
        text = "<b>📦 Daftar Produkmu</b>\n\n"
        for p in data[:10]:
            text += f"• <b>{esc_html(p.get('name'))}</b>\n  Rp{esc_html(p.get('price'))} — <code>{esc_html(p.get('code'))}</code>\n\n"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")],
            [InlineKeyboardButton("📄 Lihat Semua (browser)", callback_data="menu_product")]
        ])
        await message.reply(text, parse_mode="html", reply_markup=kb)

    # ---------- callback: menu_product -> list (compact)
    @app.on_callback_query(filters.regex("^menu_product$"))
    async def cb_menu_product(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        query = {"owner_id": user_id}
        try:
            if is_async_col(products_col):
                cursor = products_col.find(query).sort("created_at", -1)
                data = [p async for p in cursor]
            else:
                data = list(products_col.find(query).sort("created_at", -1).limit(100))
        except Exception as e:
            logger.exception("menu_product: %s", e)
            await callback.answer("Gagal memuat produk.", show_alert=True)
            return

        if not data:
            try:
                await callback.message.edit_text("📦 Belum ada produk tersedia.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]]))
            except Exception:
                pass
            await callback.answer()
            return

        # build buttons for each product (show up to 25)
        buttons = []
        for p in data[:25]:
            label = f"{p.get('name')} — Rp{p.get('price')}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"product_{esc_html(p.get('code'))}")])
        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")])
        try:
            await callback.message.edit_text("<b>📦 Pilih produk:</b>", parse_mode="html", reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as e:
            # sometimes same content causes MESSAGE_NOT_MODIFIED
            try:
                await callback.answer()
            except:
                pass

        await callback.answer()

    # ---------- callback: show product detail
    @app.on_callback_query(filters.regex(r"^product_"))
    async def cb_show_product(client: Client, callback: CallbackQuery):
        code = callback.data.split("_", 1)[1]
        user_id = callback.from_user.id
        try:
            if is_async_col(products_col):
                prod = await products_col.find_one({"code": code, "owner_id": user_id})
            else:
                prod = products_col.find_one({"code": code, "owner_id": user_id})
        except Exception as e:
            logger.exception("cb_show_product: %s", e)
            await callback.answer("Gagal memuat produk.", show_alert=True)
            return

        if not prod:
            await callback.answer("Produk tidak ditemukan.", show_alert=True)
            return

        text = (
            f"<b>🧾 Detail Produk</b>\n\n"
            f"📌 <b>{esc_html(prod.get('name'))}</b>\n"
            f"💳 Harga: Rp{esc_html(prod.get('price'))}\n"
            f"🆔 Kode: <code>{esc_html(prod.get('code'))}</code>\n\n"
            f"{esc_html(prod.get('desc','-'))}\n"
        )
        is_owner_of_prod = (prod.get("owner_id") == user_id)
        try:
            await callback.message.edit_text(text, parse_mode="html", reply_markup=product_action_buttons(prod, is_owner_of_prod))
        except Exception:
            # ignore message-not-modified
            pass
        await callback.answer()

    # ---------- callback: add_product -> start waiting for text
    @app.on_callback_query(filters.regex("^add_product$"))
    async def cb_add_product(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        # mark waiting for add
        PENDING[user_id] = {"action": "add", "code": None}
        await callback.message.edit_text(
            "🆕 <b>Tambah Produk</b>\n\n"
            "Kirim satu pesan dengan format (contoh):\n"
            "<code>Nama Produk | 25000 | KODE123 | Deskripsi singkat</code>\n\n"
            "Atau /cancel untuk membatalkan.",
            parse_mode="html"
        )
        await callback.answer("Ketik data produk sekarang (1 pesan).")

    # ---------- callback: edit product -> start edit flow
    @app.on_callback_query(filters.regex(r"^edit_product:"))
    async def cb_edit_product(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        code = callback.data.split(":",1)[1]
        # only allow owner of this product
        try:
            if is_async_col(products_col):
                prod = await products_col.find_one({"code": code, "owner_id": user_id})
            else:
                prod = products_col.find_one({"code": code, "owner_id": user_id})
        except Exception as e:
            logger.exception("edit: %s", e)
            prod = None

        if not prod:
            await callback.answer("Hanya owner produk yang boleh edit.", show_alert=True)
            return

        PENDING[user_id] = {"action": "edit", "code": code}
        await callback.message.edit_text(
            "✏️ <b>Edit Produk</b>\n\n"
            "Kirim data baru untuk produk ini dengan format:\n"
            "<code>Nama Produk | 25000 | KODE123 | Deskripsi singkat</code>\n\n"
            "Atau /cancel untuk membatalkan.",
            parse_mode="html"
        )
        await callback.answer("Ketik data baru sekarang (1 pesan).")

    # ---------- callback: delete product
    @app.on_callback_query(filters.regex(r"^delete_product:"))
    async def cb_delete_product(client: Client, callback: CallbackQuery):
        user_id = callback.from_user.id
        code = callback.data.split(":",1)[1]
        try:
            # ensure owner only
            if is_async_col(products_col):
                prod = await products_col.find_one({"code": code, "owner_id": user_id})
            else:
                prod = products_col.find_one({"code": code, "owner_id": user_id})
        except Exception as e:
            logger.exception("delete: %s", e)
            prod = None

        if not prod:
            await callback.answer("Hanya owner produk yang boleh menghapus.", show_alert=True)
            return

        try:
            if is_async_col(products_col):
                await products_col.delete_one({"code": code, "owner_id": user_id})
            else:
                products_col.delete_one({"code": code, "owner_id": user_id})
        except Exception as e:
            logger.exception("delete failed: %s", e)
            await callback.answer("Gagal menghapus produk.", show_alert=True)
            return

        try:
            await callback.message.edit_text("✅ Produk dihapus.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="menu_product")]]))
        except Exception:
            pass
        await callback.answer("Produk dihapus.")

    # ---------- message handler for pending add/edit
    @app.on_message(filters.private & ~filters.command(["start", "help", "produk"]))
    async def pending_message_handler(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id not in PENDING:
            return  # not in flow

        state = PENDING.pop(user_id)
        action = state.get("action")
        code_expected = state.get("code")

        text = message.text or ""
        parts = [p.strip() for p in text.split("|")]
        if len(parts) < 3:
            return await message.reply("❌ Format salah. Gunakan: Nama Produk | Harga | Kode | Deskripsi (opsional)")

        name = parts[0]
        price = parts[1]
        code = parts[2]
        desc = parts[3] if len(parts) > 3 else ""

        doc = {
            "name": name,
            "price": price,
            "code": code,
            "desc": desc,
            "owner_id": user_id,
            "created_at": datetime.utcnow()
        }

        try:
            if action == "add":
                # prevent duplicate code for same owner
                if is_async_col(products_col):
                    exists = await products_col.find_one({"code": code, "owner_id": user_id})
                else:
                    exists = products_col.find_one({"code": code, "owner_id": user_id})

                if exists:
                    return await message.reply("⚠️ Kode produk sudah ada. Gunakan kode lain.")

                if is_async_col(products_col):
                    await products_col.insert_one(doc)
                else:
                    products_col.insert_one(doc)

                await message.reply(f"✅ Produk ditambahkan:\n<b>{esc_html(name)}</b>\nRp{esc_html(price)}\nKode: <code>{esc_html(code)}</code>", parse_mode="html")

            elif action == "edit":
                # update by code & owner
                if is_async_col(products_col):
                    res = await products_col.update_one({"code": code, "owner_id": user_id}, {"$set": {"name": name, "price": price, "desc": desc}})
                else:
                    res = products_col.update_one({"code": code, "owner_id": user_id}, {"$set": {"name": name, "price": price, "desc": desc}})
                await message.reply(f"✅ Produk diperbarui: <b>{esc_html(name)}</b>", parse_mode="html")

        except Exception as e:
            logger.exception("pending add/edit failed: %s", e)
            await message.reply("⚠️ Terjadi kesalahan saat menyimpan produk.")

    # ---------- cancel flow
    @app.on_message(filters.command("cancel") & filters.private)
    async def cancel_flow(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id in PENDING:
            PENDING.pop(user_id, None)
            await message.reply("🔴 Flow dibatalkan.")
        else:
            await message.reply("❌ Tidak ada flow aktif.")

    logger.info("✅ handlers/product.py registered")

# handlers/menu.py
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from typing import List
import logging
import html

# try import products collection (async motor) or fallback to config.PRODUCTS
try:
    from db.mongo import products_col  # motor async collection expected
    HAS_MONGO = True
except Exception:
    products_col = None
    HAS_MONGO = False

# try fallback PRODUCTS from config
try:
    from config import PRODUCTS
except Exception:
    PRODUCTS = [
        {"code": "P1", "name": "Premium 1 Bulan", "price": "25000", "desc": "Aktif 30 hari"},
    ]

logger = logging.getLogger("handlers.menu")


def esc_html(s: str) -> str:
    if s is None:
        return ""
    return html.escape(str(s))


def is_async_collection(col) -> bool:
    # check basic: motor's find returns cursor (callable async)
    return bool(col and hasattr(col, "find") and getattr(col.find, "__call__", False) and hasattr(col, "find_one") and getattr(col.find_one, "__call__", False))


def register_menu(app):
    """
    Register menu callbacks:
      - menu_produk -> list (callback or command)
      - product_<id_or_code> -> show detail
      - back_to_start -> recreate start menu
    """

    # allow command /produk as well as callback menu button
    @app.on_message(filters.command("produk") & filters.private)
    async def cmd_produk(client, message: Message):
        await _send_product_list(client, message)

    async def _get_products_list(limit: int = 50) -> List[dict]:
        if HAS_MONGO and products_col:
            try:
                # motor async: to_list
                cursor = products_col.find().sort("created_at", -1).limit(limit)
                if hasattr(cursor, "to_list"):
                    return await cursor.to_list(length=limit)
                else:
                    # fallback: maybe sync pymongo
                    return list(cursor)
            except Exception as e:
                logger.exception("mongo get products failed: %s", e)
                return []
        else:
            return PRODUCTS

    async def _send_product_list(client, obj):
        # obj can be message or callback
        products = await _get_products_list()
        if not products:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]])
            try:
                if isinstance(obj, Message):
                    await obj.reply("📦 Belum ada produk tersedia.", reply_markup=kb)
                else:
                    # callback
                    await obj.message.edit_text("📦 Belum ada produk tersedia.", reply_markup=kb)
            except Exception:
                # ignore MESSAGE_NOT_MODIFIED etc
                pass
            return

        # build buttons (limit to 25)
        buttons = []
        for p in products[:25]:
            label = f"{p.get('name')} — Rp{p.get('price')}"
            # prefer using DB _id if present, else code
            pid = str(p.get("_id") or p.get("code"))
            buttons.append([InlineKeyboardButton(label, callback_data=f"product_{pid}")])

        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")])

        text = "📦 *Daftar Produk:*"
        try:
            if isinstance(obj, Message):
                await obj.reply(text, reply_markup=InlineKeyboardMarkup(buttons))
            else:
                # callback object
                await obj.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
                await obj.answer()
        except Exception:
            # swallow MESSAGE_NOT_MODIFIED and others
            try:
                await obj.answer()
            except:
                pass

    # callback entrypoint for menu_produk button
    @app.on_callback_query(filters.regex("^menu_produk$"))
    async def cb_menu_produk(client, callback: CallbackQuery):
        await _send_product_list(client, callback)

    # show detail for each product (callback_data "product_<id_or_code>")
    @app.on_callback_query(filters.regex(r"^product_"))
    async def show_product_detail(client, callback: CallbackQuery):
        identifier = callback.data.split("_", 1)[1]
        prod = None

        # try fetch from mongo by _id or code
        if HAS_MONGO and products_col:
            try:
                # try by ObjectId-like first (but safe fallback)
                # use find_one directly with either _id as string or code
                prod = await products_col.find_one({"_id": identifier})
                if not prod:
                    prod = await products_col.find_one({"code": identifier})
            except Exception as e:
                logger.debug("mongo lookup error, fallback to config list: %s", e)
                prod = None

        if not prod:
            # fallback to in-memory PRODUCTS list
            prod = next((x for x in PRODUCTS if str(x.get("_id") or x.get("code")) == identifier or x.get("code") == identifier), None)

        if not prod:
            try:
                await callback.answer("Produk tidak ditemukan!", show_alert=True)
            except:
                pass
            return

        # prepare text (use simple formatting, not forcing parse_mode to avoid parse errors)
        text_lines = [
            "🧾 Tagihan Premium",
            "",
            f"📌 Produk: {esc_html(prod.get('name'))}",
            f"💳 Harga: Rp{esc_html(prod.get('price'))}",
            f"🆔 Kode: {esc_html(str(prod.get('code') or prod.get('_id')))}",
            "",
            esc_html(prod.get("desc", "-")),
        ]
        text = "\n".join(text_lines)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Konfirmasi Pembayaran", callback_data=f"confirm_{identifier}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_produk")]
        ])

        try:
            await callback.message.edit_text(text, reply_markup=kb)
            await callback.answer()
        except Exception:
            # message not modified or parse error -> try answer only
            try:
                await callback.answer()
            except:
                pass

    # back to start menu (recreate main start; rely on handlers.start to present start keyboard)
    @app.on_callback_query(filters.regex("^back_to_start$"))
    async def back_to_start_cb(client, callback: CallbackQuery):
        try:
            # if you have start handler that responds to /start, re-run it by sending a new start message
            # but safest: edit to a simple prompt with button to call /start
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali ke Start", callback_data="menu_start")]])
            await callback.message.edit_text("🔙 Kembali ke menu utama.", reply_markup=kb)
            await callback.answer()
        except Exception:
            try:
                await callback.answer()
            except:
                pass

    # optional: a tiny handler to instruct user to press /start (menu_start)
    @app.on_callback_query(filters.regex("^menu_start$"))
    async def menu_start_cb(client, callback: CallbackQuery):
        try:
            # call the start handler by sending /start (safer to send a new message)
            await callback.message.reply("/start")
            await callback.answer()
        except Exception:
            try:
                await callback.answer()
            except:
                pass

    logger.info("✅ handlers/menu.py registered")

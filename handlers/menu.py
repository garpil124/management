from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
import logging
from config import PRODUCTS if hasattr(import('config'), 'PRODUCTS') else []

logger = logging.getLogger("Handlers")

# We'll keep PRODUCTS local for compatibility if not in DB
PRODUCTS = getattr(import('config'), 'PRODUCTS', [
    {"code": "P1", "name": "Premium 1 Bulan", "price": "25000", "desc":"Aktif 30 hari"},
])

def escape_md_v2(s: str):
    # minimal escaping for MarkdownV2
    for ch in r'\_*[]()~`>#+-=|{}.!':
        s = s.replace(ch, "\\"+ch)
    return s

def register_menu(app: Client):
    @app.on_callback_query(filters.regex("^menu_produk"))
    async def menu_produk_cb(client: Client, callback: CallbackQuery):
        try:
            buttons = []
            for p in PRODUCTS:
                buttons.append([InlineKeyboardButton(f"{p['name']} — Rp{p['price']}", callback_data=f"product_{p['code']}")])
            buttons.append([InlineKeyboardButton("⬅ Kembali", callback_data="back_to_start")])
            await callback.message.edit_text("📦 Pilih produk:", reply_markup=InlineKeyboardMarkup(buttons))
            await callback.answer()
        except Exception as e:
            logger.exception("menu_produk error: %s", e)
            await callback.answer("Gagal memuat produk.", show_alert=True)

    @app.on_callback_query(filters.regex(r"^product_"))
    async def show_product_detail(client: Client, callback: CallbackQuery):
        try:
            code = callback.data.split("_",1)[1]
            prod = next((x for x in PRODUCTS if x["code"] == code), None)
            if not prod:
                await callback.answer("Produk tidak ditemukan.", show_alert=True)
                return
            text = (
                f"🧾 *Tagihan Premium*\n\n"
                f"📌 *Produk:* {escape_md_v2(prod['name'])}\n"
                f"💳 *Harga:* Rp{escape_md_v2(prod['price'])}\n"
                f"🆔 *Kode:* {escape_md_v2(prod['code'])}\n\n"
                f"{escape_md_v2(prod.get('desc','-'))}\n\n"
                "✅ Tekan tombol di bawah untuk melanjutkan pembayaran."
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Konfirmasi Pembayaran", callback_data=f"confirm_{prod['code']}")],
                [InlineKeyboardButton("⬅ Kembali", callback_data="menu_produk")]
            ])
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="MarkdownV2")
            await callback.answer()
        except Exception as e:
            logger.exception("show_product_detail error: %s", e)
            await callback.answer("Gagal menampilkan detail.", show_alert=True)

    @app.on_callback_query(filters.regex("^back_to_start$"))
    async def back_to_start_cb(client: Client, callback: CallbackQuery):
        try:
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📦 Produk", callback_data="menu_produk")]])
            await callback.message.edit_text("👋 Kembali ke menu:", reply_markup=buttons)
            await callback.answer()
        except Exception as e:
            logger.exception("back_to_start error: %s", e)

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import escape_md_v2, escape_md_v2 as esc
from config import OWNER_ID
import logging

logger = logging.getLogger("menu")

PRODUCTS = [
    {"code": "P1", "name": "Premium 1 Bulan", "price": "25000", "desc": "Aktif 30 hari"},
    {"code": "P3", "name": "Premium 3 Bulan", "price": "60000", "desc": "Aktif 90 hari"}
]

def register_menu(app: Client):
    @app.on_callback_query(filters.regex("^menu_produk$"))
    async def menu_produk_cb(client: Client, callback: CallbackQuery):
        try:
            buttons = []
            for p in PRODUCTS:
                buttons.append([InlineKeyboardButton(f"{p['name']} — Rp{p['price']}", callback_data=f"product_{p['code']}")])
            buttons.append([InlineKeyboardButton("⬅ Kembali", callback_data="back_to_start")])
            await callback.message.edit_text("📦 Daftar Produk:", reply_markup=InlineKeyboardMarkup(buttons))
            await callback.answer()
        except Exception as e:
            logger.exception("menu_produk_cb: %s", e)
            await callback.answer("Gagal memuat produk", show_alert=True)

    @app.on_callback_query(filters.regex("^product_"))
    async def show_product_detail(client: Client, callback: CallbackQuery):
        try:
            code = callback.data.replace("product_", "")
            product = next((p for p in PRODUCTS if p["code"] == code), None)
            if not product:
                await callback.answer("Produk tidak ditemukan", show_alert=True)
                return
            text = (
                "🧾 *Tagihan Premium*\n\n"
                f"📌 *Produk:* {escape_md_v2(product['name'])}\n"
                f"💳 *Harga:* Rp{escape_md_v2(product['price'])}\n"
                f"🆔 *Kode:* {escape_md_v2(product['code'])}\n\n"
                f"{escape_md_v2(product.get('desc','-'))}\n\n"
                "✅ Tekan tombol di bawah untuk melanjutkan pembayaran."
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Konfirmasi Pembayaran", callback_data=f"confirm_{product['code']}")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_produk")]
            ])
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="MarkdownV2")
            await callback.answer()
        except Exception as e:
            logger.exception("show_product_detail: %s", e)
            await callback.answer("Gagal tampilkan detail", show_alert=True)

    @app.on_callback_query(filters.regex("^confirm_"))
    async def confirm_product_cb(client: Client, callback: CallbackQuery):
        try:
            await callback.message.edit_text("🔔 Kirim bukti pembayaran sebagai balasan foto lalu gunakan perintah:\n/confirm <ORDER_ID>")
            await callback.answer()
        except Exception as e:
            logger.exception("confirm_product_cb: %s", e)
            await callback.answer("Gagal", show_alert=True)

    @app.on_callback_query(filters.regex("^back_to_start$"))
    async def back_to_start_cb(client: Client, callback: CallbackQuery):
        try:
            await callback.message.edit_text("👋 Kembali ke menu utama.", reply_markup=None)
            await callback.answer()
        except Exception as e:
            logger.exception("back_to_start: %s", e)
            await callback.answer("Gagal", show_alert=True)

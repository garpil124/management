from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from util.helpers import escape_markdown_v2
from config import PRODUCTS
import logging

logger = logging.getLogger('product')


def register_product(app):

    @app.on_callback_query(filters.regex(r'^product_'))
    async def show_product_detail(client, callback: CallbackQuery):
        try:
            code = callback.data.split('product_', 1)[1]
            product = next((p for p in PRODUCTS if p['code'] == code), None)
            if not product:
                await callback.answer('Produk tidak ditemukan.', show_alert=True)
                return

            # Build MarkdownV2-safe text
            name = escape_markdown_v2(product.get('name'))
            price = escape_markdown_v2(product.get('price'))
            code_s = escape_markdown_v2(product.get('code'))
            desc = escape_markdown_v2(product.get('desc', 'Tidak ada deskripsi.'))

            text = (
                f"🧾 *Tagihan Premium*\n\n"
                f"📌 *Produk:* {name}\n"
                f"💳 *Harga:* Rp{price}\n"
                f"🆔 *Kode:* {code_s}\n\n"
                f"{desc}\n\n"
                "✅ Tekan tombol di bawah untuk melanjutkan pembayaran."
            )

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton('✅ Konfirmasi Pembayaran', callback_data=f'confirm_{code_s}')],
                [InlineKeyboardButton('⬅ Kembali', callback_data='menu_produk')]
            ])

            await callback.message.edit_text(text, reply_markup=buttons, parse_mode='MarkdownV2')
            await callback.answer()
        except Exception as e:
            logger.exception('show_product_detail error: %s', e)
            await callback.answer('⚠️ Gagal menampilkan detail.', show_alert=True)

    @app.on_callback_query(filters.regex(r'^confirm_'))
    async def confirm_product_cb(client, callback: CallbackQuery):
        try:
            code = callback.data.split('confirm_', 1)[1]
            text = (
                "🔔 *Instruksi Pembayaran*\n\n"
                "Silakan transfer / bayar sesuai instruksi yang telah disediakan.\n\n"
                "Setelah membayar, upload bukti (foto) lalu gunakan perintah:\n"
                "/confirm <ORDER_ID>\n\nOrder ID dibuat setelah proses pembelian."
            )
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅ Kembali', callback_data='menu_produk')]]), parse_mode='MarkdownV2')
            await callback.answer()
        except Exception as e:
            logger.exception('confirm_product_cb error: %s', e)
            await callback.answer('⚠️ Gagal menampilkan instruksi.', show_alert=True)

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from database.mongo import payments, products, users

# === KEYBOARD KONFIRMASI BAYAR ===
def payment_kb(pid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Saya Sudah Bayar", callback_data=f"pay:confirm:{pid}")],
        [InlineKeyboardButton("🔙 Batal", callback_data="prod:list")]
    ])

@Client.on_callback_query(filters.regex("^pay:"))
async def payment_cb(client: Client, cb: CallbackQuery):

    data = cb.data

    # USER PILIH BAYAR PRODUK
    if data.startswith("pay:product:"):
        pid = data.split(":")[2]
        product = await products.find_one({"_id": pid})

        if not product:
            return await cb.answer("❌ Produk tidak ditemukan", True)

        text = (
            f"💰 **Pembayaran Produk**\n\n"
            f"🛍 Produk: {product['name']}\n"
            f"💸 Harga: Rp {product['price']}\n\n"
            f"Silakan transfer ke metode yang tersedia,\n"
            f"lalu klik **'Saya Sudah Bayar'** dan kirim bukti pembayaran."
        )

        await cb.message.edit_text(text, reply_markup=payment_kb(pid))

    # USER KONFIRM SUDAH BAYAR
    elif data.startswith("pay:confirm:"):
        pid = data.split(":")[2]
        product = await products.find_one({"_id": pid})
        if not product:
            return await cb.answer("❌ Produk tidak ditemukan", True)

        # Simpan payment ke database status pending
        pay_data = {
            "user_id": cb.from_user.id,
            "product_id": pid,
            "product_name": product["name"],
            "price": product["price"],
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        await payments.insert_one(pay_data)

        msg = (
            "✅ Permintaan pembayaran dicatat!\n\n"
            "📎 Silakan kirim **bukti transfer / screenshot pembayaran** di sini.\n"
            "Admin akan segera verifikasi."
        )

        await cb.message.edit_text(msg)

    await cb.answer()

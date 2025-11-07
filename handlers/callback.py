from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from config import OWNER_ID

@Client.on_callback_query()
async def cb_handler(client: Client, cb: CallbackQuery):

    data = cb.data

    # ===== MENU OWNER CALLBACK =====
    if data == "owner:panel":
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("⛔ Bukan akses kamu!", show_alert=True)

        txt = (
            "👑 Owner Control Panel\n\n"
            "Pilih menu di bawah:"
        )
        await cb.message.edit_text(txt, reply_markup=owner_kb())

    # ===== MENU PREMIUM =====
    elif data == "premium:info":
        txt = (
            "⭐ Premium User Plan ⭐\n\n"
            "⏳ Durasi : 30 Hari\n"
            "⚡ Benefit :\n"
            "• Akses semua fitur premium\n"
            "• Limit lebih besar\n"
            "• Support prioritas\n\n"
            "Klik tombol di bawah untuk beli!"
        )
        await cb.message.edit_text(txt, reply_markup=premium_kb())

    # ===== PAYMENT CONFIRMATION =====
    elif data.startswith("pay:"):
        payment_method = data.split(":")[1]
        await cb.message.edit_text(
            f"💳 Kamu memilih metode: {payment_method.upper()}\n\n"
            "Silakan upload bukti pembayaran (foto/screenshot)."
        )

    # ===== BACK MENU =====
    elif data == "menu:back":
        await cb.message.edit_text("🔙 Kembali ke menu utama", reply_markup=main_kb())

    await cb.answer()

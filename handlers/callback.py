from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID

# ===== KEYBOARD DEFINITIONS =====

def owner_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 List Partner", callback_data="owner:list_partners")],
        [InlineKeyboardButton("⭐ Premium List", callback_data="owner:list_premium")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu:back")]
    ])

def premium_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Bayar (QRIS)", callback_data="pay:qris")],
        [InlineKeyboardButton("💳 Bayar (DANA)", callback_data="pay:dana")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu:back")]
    ])

def main_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍 Produk", callback_data="menu_product"),
            InlineKeyboardButton("💳 Payment", callback_data="menu_payment"),
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="premium:info"),
            InlineKeyboardButton("📘 Bantuan", callback_data="menu_help"),
        ],
        [InlineKeyboardButton("👥 Support", url="https://t.me/storegarf")],
    ])

# ===== CALLBACK HANDLER =====

@Client.on_callback_query()
async def cb_handler(client: Client, cb: CallbackQuery):

    data = cb.data

    # ===== MENU OWNER CALLBACK =====
    if data == "menu_owner":
        if cb.from_user.id != OWNER_ID:
            return await cb.answer("⛔️ Bukan akses kamu!", show_alert=True)

        txt = "👑 *Owner Control Panel*\n\nPilih menu di bawah:"
        await cb.message.edit_text(txt, reply_markup=owner_kb())

    # ===== PREMIUM MENU =====
    elif data == "menu_premium":
        txt = (
            "⭐️ *Premium User Plan* ⭐️\n\n"
            "⏳ Durasi : 30 Hari\n"
            "⚡ Benefit :\n"
            "• Akses semua fitur premium\n"
            "• Limit lebih besar\n"
            "• Support prioritas\n\n"
            "Klik tombol di bawah untuk beli!"
        )
        await cb.message.edit_text(txt, reply_markup=premium_kb())

    # ===== PAYMENT CONFIRM =====
    elif data.startswith("pay:"):
        method = data.split(":")[1].upper()
        await cb.message.edit_text(
            f"💳 Kamu memilih metode pembayaran: {method}\n\n"
            "Silakan kirim bukti pembayaran (foto/screenshot)."
        )

    # ===== BACK MENU =====
    elif data == "menu:back":
        await cb.message.edit_text("🔙 *Kembali ke menu utama*", reply_markup=main_kb())

    await cb.answer()

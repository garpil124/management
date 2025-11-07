from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Premium", callback_data="premium:info")],
        [InlineKeyboardButton("👑 Owner Panel", callback_data="owner:panel")]
    ])

def owner_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Produk", callback_data="owner:products")],
        [InlineKeyboardButton("💰 Payment", callback_data="owner:payment")],
        [InlineKeyboardButton("⭐ Premium List", callback_data="owner:premiumlist")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu:back")]
    ])

def premium_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Bayar - DANA", callback_data="pay:dana")],
        [InlineKeyboardButton("💳 Bayar - GOPAY", callback_data="pay:gopay")],
        [InlineKeyboardButton("💳 Bayar - QRIS", callback_data="pay:qris")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu:back")]
    ])

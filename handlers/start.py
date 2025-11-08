from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from config import OWNER_ID

CREATOR = os.getenv("CREATOR_NAME", "Unknown")

@Client.on_message(filters.command("start"))
async def start_bot(client, message):
    user = message.from_user
    mention = user.mention if user else "Unknown"
    user_id = user.id if user else 0
    is_owner = user_id == OWNER_ID

    # ===== MESSAGE TEXT =====
    text = f"""
👋 Halo {mention}  
🤖 *Saya adalah Management Bot*  
👑 Creator: {CREATOR}

📌 Silakan pilih menu di bawah :
"""

    if is_owner:
        text += "\n⚠️ Kamu login sebagai OWNER\n"

    # ===== BUTTONS =====
    buttons = [
        [
            InlineKeyboardButton("🛍 Produk", callback_data="menu_product"),
            InlineKeyboardButton("💳 Payment", callback_data="menu_payment"),
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="menu_premium"),
            InlineKeyboardButton("📘 Bantuan", callback_data="menu_help"),
        ],
        [
            InlineKeyboardButton("👥 Support", url="https://t.me/storegarf")
        ]
    ]

    # Tambah admin panel jika owner
    if is_owner:
        buttons.append([
            InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu_owner")
        ])

    # ===== SEND MESSAGE =====
    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

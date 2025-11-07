from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

CREATOR = os.getenv("CREATOR_NAME", "Unknown")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

@Client.on_message(filters.command("start"))
async def start_bot(client, message):

    user = message.from_user
    mention = user.mention if user else "Unknown"

    is_owner = user and user.id == OWNER_ID

    # Text welcome
    text = f"""
👋 Halo {mention}!
🤖 Saya adalah Management Bot
👑 Creator: {CREATOR}

📌 Gunakan tombol di bawah untuk mulai.
"""

    if is_owner:
        text += "\n⚠ Kamu login sebagai OWNER\n"

    # Button menu
    buttons = [
        [
            InlineKeyboardButton("🛍 Produk",    callback_data="menu_product"),
            InlineKeyboardButton("💳 Payment",   callback_data="menu_payment"),
        ],
        [
            InlineKeyboardButton("⭐ Premium",   callback_data="menu_premium"),
            InlineKeyboardButton("🧾 Bantuan",  callback_data="menu_help"),
        ]
    ]

    # Button owner only
    if is_owner:
        buttons.append([
            InlineKeyboardButton("⚙ Admin Panel", callback_data="menu_owner")
        ])

    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

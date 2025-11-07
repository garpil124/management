# handlers/help.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, CREATOR_NAME

@Client.on_message(filters.command("help"))
async def help_cmd(client, message):
    uid = message.from_user.id if message.from_user else None

    if uid == OWNER_ID:
        text = (
            "<b>👑 Owner Menu</b>\n\n"
            "/addpartner <BOT_TOKEN> <LOG_GROUP> <STORE_NAME> - tambah partner/sub-owner\n"
            "/listpartners - list partner\n"
            "/delpartner <partner_id> - hapus partner\n"
            "/listprem - list premium users\n"
            "/addprem <user_id> - beri premium manual\n"
            "/backup - buat backup manual\n"
        )
        kb = [
            [InlineKeyboardButton("Manage Partners", callback_data="owner:partners")],
            [InlineKeyboardButton("View Backups", callback_data="owner:backups")]
        ]
    else:
        text = (
            f"<b>🤖 Garfield Store</b>\nCreator: {CREATOR_NAME}\n\n"
            "Gunakan tombol di bawah untuk melihat katalog atau cek status premium."
        )
        kb = [
            [InlineKeyboardButton("📦 Lihat Katalog", callback_data="cat:None:0")],
            [InlineKeyboardButton("💎 Cek Premium", callback_data="user:prem")]
        ]

    await message.reply(text, reply_markup=InlineKeyboardMarkup(kb), quote=True)

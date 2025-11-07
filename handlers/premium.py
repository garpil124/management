# handlers/premium.py
from pyrogram import Client, filters
from db.mongo import users_col
import datetime

@Client.on_message(filters.command("status") & filters.private)
async def premium_status(client, message):
    uid = message.from_user.id
    doc = await users_col.find_one({"user_id": uid})
    if not doc or not doc.get("is_premium"):
        return await message.reply("🔓 Kamu bukan premium user.")
    until = doc.get("premium_until")
    if until:
        return await message.reply(f"✅ Premium aktif hingga: {until}")
    else:
        return await message.reply("✅ Premium aktif (no expiry set).")

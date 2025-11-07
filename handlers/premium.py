from pyrogram import Client, filters
from config import OWNER_ID
from db.premium import add_premium, remove_premium, get_premium, is_premium
from datetime import datetime

@Client.on_message(filters.command("addprem") & filters.user(OWNER_ID))
async def cmd_addprem(_, m):
    try:
        user_id = int(m.command[1])
        days = int(m.command[2]) if len(m.command) > 2 else 30
        exp = await add_premium(user_id, days)
        await m.reply(f"✅ Premium diaktifkan untuk {user_id} sampai:\n{exp}")
    except:
        await m.reply("Format salah!\nContoh: /addprem 12345678 30")

@Client.on_message(filters.command("delprem") & filters.user(OWNER_ID))
async def cmd_delprem(_, m):
    try:
        user_id = int(m.command[1])
        await remove_premium(user_id)
        await m.reply(f"🗑 Premium dihapus untuk {user_id}")
    except:
        await m.reply("Format salah!\nContoh: /delprem 12345678")

@Client.on_message(filters.command("cekprem"))
async def cmd_cekprem(_, m):
    user_id = m.from_user.id
    data = await get_premium(user_id)
    if not data:
        return await m.reply("❌ Kamu bukan user premium.")
    exp = data["expired"]
    await m.reply(f"⭐ Kamu user premium sampai:\n{exp}")

@Client.on_message(filters.command("premuser") & filters.user(OWNER_ID))
async def cmd_listprem(_, m):
    text = "⭐ Daftar User Premium:\n\n"
    async for u in get_all_premium():
        text += f"• {u['user_id']} → {u['expired']}\n"
    await m.reply(text)

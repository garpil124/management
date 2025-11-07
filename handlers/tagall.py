# handlers/tagall.py
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
import asyncio

@Client.on_message(filters.command("tagall") & (filters.group | filters.supergroup))
async def tagall_handler(client: Client, message: Message):
    chat = message.chat
    user = message.from_user

    # Cek hanya owner yg boleh pakai
    if user.id != OWNER_ID:
        return await message.reply("⛔ Perintah ini hanya untuk Owner!")

    msg = message.text.split(" ", 1)
    alasan = msg[1] if len(msg) > 1 else "Ada pengumuman penting!"

    await message.reply("🔔 Tagall dimulai...")

    members = []
    async for m in client.get_chat_members(chat.id):
        if not m.user.is_bot:
            members.append(m.user)

    chunk = 5  # Tag 5 orang per pesan biar gak flood ban
    for i in range(0, len(members), chunk):
        teks = f"📢 {alasan}\n\n"
        for u in members[i:i+chunk]:
            mention = u.mention if u.username else f"[{u.first_name}](tg://user?id={u.id})"
            teks += mention + " "

        await client.send_message(chat.id, teks)
        await asyncio.sleep(2)  # Anti flood

    await message.reply("✅ Tagall selesai!")

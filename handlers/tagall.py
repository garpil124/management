# handlers/tagall.py
from pyrogram import Client, filters
from utils.helpers import send_log

@Client.on_message(filters.command("tagall") & filters.group)
async def tagall(client, message):
    chat_id = message.chat.id
    members = []
    async for m in client.get_chat_members(chat_id, filter="administrators"):
        if m.user and not m.user.is_bot:
            members.append(m.user.id)

    if not members:
        return await message.reply("⚠️ Tidak ada admin ditemukan.")

    # mention in batches of 5
    batch = []
    for i, uid in enumerate(members, start=1):
        batch.append(f"[👤](tg://user?id={uid})")
        if i % 5 == 0:
            await message.reply(" ".join(batch))
            batch = []
    if batch:
        await message.reply(" ".join(batch))

    await message.reply(f"✅ Selesai memanggil {len(members)} admin.")

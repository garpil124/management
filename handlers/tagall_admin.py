from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

def register_tagall_admin(app: Client):

    @app.on_message(filters.command("tagall") & filters.group)
    async def tagall_admin(client: Client, message: Message):

        # Cek apakah pengirim admin
        user = await client.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in ["administrator", "creator"]:
            return await message.reply("❌ Hanya admin yang bisa pakai perintah ini!")

        text = message.text.split(" ", 1)
        custom_text = text[1] if len(text) > 1 else "Halo semuanya!"

        await message.reply("📢 Memanggil semua member...")

        mentions = []
        async for member in client.get_chat_members(message.chat.id):
            if not member.user.is_bot:
                mentions.append(member.user.mention)

        if not mentions:
            return await message.reply("⚠ Tidak ada member untuk di-tag!")

        msg = f"📣 {custom_text}\n\n"

        for i, user in enumerate(mentions):
            msg += user + "  "
            # Kirim tiap 5 mention biar gak flood
            if (i + 1) % 5 == 0:
                await message.reply(msg)
                await asyncio.sleep(1.5)
                msg = ""

        if msg.strip():
            await message.reply(msg)

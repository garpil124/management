from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from db.mongo import partners_col
from utils.tools import safe_send
import time


@Client.on_message(filters.command("addsub") & filters.user(OWNER_ID))
async def add_subowner(client: Client, message: Message):
    try:
        args = message.text.split()
        # Format:
        # /addsub BOT_TOKEN LOG_GROUP_ID MAIN_GROUP_ID NAMA_OWNER_BOT
        if len(args) < 5:
            await message.reply(
                "<b>Format salah!</b>\n"
                "<code>/addsub BOT_TOKEN LOG_GROUP_ID MAIN_GROUP_ID NAMA_OWNER</code>"
            )
            return

        bot_token   = args[1]
        log_group   = int(args[2])
        main_group  = int(args[3])
        owner_name  = " ".join(args[4:])

        data = {
            "bot_token": bot_token,
            "log_group": log_group,
            "main_group": main_group,
            "owner_name": owner_name,
            "created_at": int(time.time()),
            "premium_until": None
        }

        # Simpan ke database
        await partners_col.insert_one(data)

        await message.reply(
            f"<b>✅ Sub-Owner Ditambah!</b>\n"
            f"Nama : <code>{owner_name}</code>\n"
            f"Log   : <code>{log_group}</code>\n"
            f"Grup  : <code>{main_group}</code>\n\n"
            "Bot akan otomatis aktif dengan token yang diberikan."
        )

    except Exception as e:
        await message.reply(f"❌ Error addsub: <code>{str(e)}</code>")


@Client.on_message(filters.command("listsub") & filters.user(OWNER_ID))
async def list_subowners(client: Client, message: Message):
    subs = []
    async for s in partners_col.find({}):
        subs.append(
            f"👤 {s['owner_name']}\n"
            f"├ Token : <code>{s['bot_token'][:10]}***</code>\n"
            f"├ Log   : <code>{s['log_group']}</code>\n"
            f"└ Grub  : <code>{s['main_group']}</code>\n"
        )

    if not subs:
        return await message.reply("⚠️ Belum ada sub-owner tersimpan.")

    txt = "<b>📋 Daftar Sub-Owner:</b>\n\n" + "\n".join(subs)
    await message.reply(txt)


@Client.on_message(filters.command("delsub") & filters.user(OWNER_ID))
async def del_subowner(client: Client, message: Message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("<b>Format:</b> <code>/delsub BOT_TOKEN</code>")

    bot_token = args[1]
    res = await partners_col.delete_one({"bot_token": bot_token})

    if res.deleted_count:
        await message.reply("✅ Sub-Owner berhasil dihapus!")
    else:
        await message.reply("⚠️ Token tidak ditemukan di database.")

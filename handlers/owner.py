from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from db.mongo import partners_col
from utils.helpers import safe_send
import datetime
import logging
logger = logging.getLogger("owner")

def register_owner(app: Client):
    @app.on_message(filters.command("addpartner") & filters.user(OWNER_ID) & filters.private)
    async def add_partner(client, message: Message):
        # /addpartner <BOT_TOKEN> <LOG_GROUP_ID> <STORE_NAME>
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            return await message.reply("Usage: /addpartner <BOT_TOKEN> <LOG_GROUP_ID> <STORE_NAME>")
        _, token, log_group, store_name = parts
        try:
            log_group = int(log_group)
        except:
            return await message.reply("LOG_GROUP harus angka.")
        doc = {
            "bot_token": token,
            "log_group": log_group,
            "store_name": store_name,
            "created_at": datetime.datetime.utcnow(),
            "enabled": True
        }
        await partners_col.insert_one(doc)
        await message.reply("✅ Partner ditambahkan.")

    @app.on_message(filters.command("listpartners") & filters.user(OWNER_ID) & filters.private)
    async def list_partners(client, message: Message):
        rows = []
        async for r in partners_col.find().sort("created_at", -1):
            rows.append(f"{r.get('_id')} — {r.get('store_name')} — log:{r.get('log_group')}")
        await message.reply("📦 Partners:\n" + ("\n".join(rows) if rows else "Tidak ada"))

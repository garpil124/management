# handlers/owner.py
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from db.mongo import partners_col, users_col, backup_col
from utils.helpers import send_log
from bson.objectid import ObjectId
import datetime

@Client.on_message(filters.command("addpartner") & filters.user(OWNER_ID) & filters.private)
async def add_partner(client: Client, message: Message):
    """
    /addpartner <BOT_TOKEN> <LOG_GROUP> <STORE_NAME>
    """
    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 4:
            return await message.reply("Usage: /addpartner <BOT_TOKEN> <LOG_GROUP> <STORE_NAME>")

        _, bot_token, log_group, store_name = args
        doc = {
            "token": bot_token,
            "log_group": int(log_group),
            "store": store_name,
            "owner_id": message.from_user.id,
            "created_at": datetime.datetime.utcnow()
        }
        res = await partners_col.insert_one(doc)
        await message.reply(f"✅ Partner created: {res.inserted_id}")
        await send_log(client, f"Owner added partner {store_name} id:{res.inserted_id}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@Client.on_message(filters.command("listpartners") & filters.user(OWNER_ID) & filters.private)
async def list_partners(client: Client, message: Message):
    rows = []
    async for r in partners_col.find().sort("created_at", -1):
        rows.append(f"{r.get('_id')} — {r.get('store')} — log:{r.get('log_group')}")
    text = "<b>Partner List</b>\n\n" + ("\n".join(rows) if rows else "No partners yet.")
    await message.reply(text)

@Client.on_message(filters.command("delpartner") & filters.user(OWNER_ID) & filters.private)
async def del_partner(client: Client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply("Usage: /delpartner <partner_object_id>")
        pid = parts[1]
        try:
            oid = ObjectId(pid)
        except:
            return await message.reply("Invalid partner id format")

        await partners_col.delete_one({"_id": oid})
        await message.reply("✅ Partner removed")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@Client.on_message(filters.command("addprem") & filters.user(OWNER_ID) & filters.private)
async def add_premium_manual(client: Client, message: Message):
    """
    /addprem <user_id>
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply("Usage: /addprem <user_id>")
        uid = int(parts[1])
        import datetime
        until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        await users_col.update_one({"user_id": uid}, {"$set": {"is_premium": True, "premium_until": until}}, upsert=True)
        await message.reply(f"✅ User {uid} set premium until {until.isoformat()}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@Client.on_message(filters.command("listprem") & filters.user(OWNER_ID) & filters.private)
async def list_prem(client: Client, message: Message):
    rows = []
    async for u in users_col.find({"is_premium": True}):
        rows.append(f"{u.get('user_id')} — until: {u.get('premium_until')}")
    await message.reply("<b>Premium Users</b>\n\n" + ("\n".join(rows) if rows else "No premium users"))

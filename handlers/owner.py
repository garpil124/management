# handlers/owner.py
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from db.mongo import partners_col, users_col
from utils.helpers import send_log
from bson.objectid import ObjectId
import datetime

def register_(app):

    @app.on_message(filters.command("addpartner") & filters.user(OWNER_ID) & filters.private)
    async def add_partner(client: Client, message: Message):
        """
        /addpartner <BOT_TOKEN> <LOG_GROUP_ID> <STORE_NAME>
        """
        try:
            args = message.text.split(maxsplit=3)
            if len(args) < 4:
                return await message.reply("Usage: /addpartner <BOT_TOKEN> <LOG_GROUP_ID> <STORE_NAME>")

            _, bot_token, log_group, store_name = args

            # validasi format token sederhana
            if ":" not in bot_token or len(bot_token) < 30:
                return await message.reply("❌ Bot token tidak valid!")

            doc = {
                "token": bot_token,
                "log_group": int(log_group),
                "store": store_name,
                "owner_id": message.from_user.id,
                "created_at": datetime.datetime.utcnow()
            }

            res = await partners_col.insert_one(doc)
            await message.reply(f"✅ Partner created!\nStore: {store_name}\nID: {res.inserted_id}")

            await send_log(client, f"🆕 Owner added partner <b>{store_name}</b>\nID: <code>{res.inserted_id}</code>")

        except Exception as e:
            await message.reply(f"❌ Error: {e}")


    @app.on_message(filters.command("listpartners") & filters.user(OWNER_ID) & filters.private)
    async def list_partners(client: Client, message: Message):
        rows = []
        async for r in partners_col.find().sort("created_at", -1):
            rows.append(
                f"🟢 {r['_id']}\n"
                f"🏬 Store: {r['store']}\n"
                f"📢 Log Group: {r['log_group']}\n"
                "--------------------"
            )

        text = "📌 <b>Partner List</b>\n\n" + ("\n".join(rows) if rows else "Belum ada partner.")
        await message.reply(text)


    @app.on_message(filters.command("delpartner") & filters.user(OWNER_ID) & filters.private)
    async def del_partner(client: Client, message: Message):
        try:
            parts = message.text.split()
            if len(parts) < 2:
                return await message.reply("Usage: /delpartner <partner_object_id>")

            try:
                oid = ObjectId(parts[1])
            except:
                return await message.reply("❌ Format ID salah!")

            await partners_col.delete_one({"_id": oid})
            await message.reply("✅ Partner berhasil dihapus")

        except Exception as e:
            await message.reply(f"❌ Error: {e}")


    @app.on_message(filters.command("addprem") & filters.user(OWNER_ID) & filters.private)
    async def add_premium_manual(client: Client, message: Message):
        """
        /addprem <user_id>
        """
        try:
            parts = message.text.split()
            if len(parts) < 2:
                return await message.reply("Usage: /addprem <user_id>")

            uid = int(parts[1])
            until = datetime.datetime.utcnow() + datetime.timedelta(days=30)

            await users_col.update_one(
                {"user_id": uid},
                {"$set": {"is_premium": True, "premium_until": until}},
                upsert=True
            )

            await message.reply(f"✅ User {uid} sekarang premium\n🗓 Until: {until}")

        except Exception as e:
            await message.reply(f"❌ Error: {e}")


    @app.on_message(filters.command("listprem") & filters.user(OWNER_ID) & filters.private)
    async def list_prem(client: Client, message: Message):
        rows = []
        async for u in users_col.find({"is_premium": True}):
            rows.append(f"{u['user_id']} → until: {u['premium_until']}")

        await message.reply("⭐ <b>Premium Users</b>\n\n" + ("\n".join(rows) if rows else "Belum ada user premium"))

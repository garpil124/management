from pyrogram import Client, filters
from pyrogram.types import Message
from db.mongo import orders_col, payments_col, products_col, users_col
from bson.objectid import ObjectId
import datetime
import os
import logging

logger = logging.getLogger("payment")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def register_payment(app: Client):

    @app.on_message(filters.command("confirm") & filters.private)
    async def confirm_pay(client, message: Message):
        try:
            parts = message.text.split()
            if len(parts) < 2:
                return await message.reply("Format: reply foto bukti > /confirm <ORDER_ID>")

            oid = parts[1]
            if not message.reply_to_message or not message.reply_to_message.photo:
                return await message.reply("❌ Reply ke foto bukti pembayaran.")

            fpath = await message.reply_to_message.download(file_name=os.path.join(UPLOAD_FOLDER, f"proof_{message.from_user.id}_{oid}.jpg"))

            # update order
            await orders_col.update_one({"_id": ObjectId(oid)}, {"$set": {"payment_proof": fpath, "status": "paid", "paid_at": datetime.datetime.utcnow()}})

            ord_doc = await orders_col.find_one({"_id": ObjectId(oid)})
            prod = await products_col.find_one({"code": ord_doc.get("product_code")}) if ord_doc else None

            # if premium -> give premium 30 days
            if prod and 'premium' in prod.get('name','').lower():
                until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
                await users_col.update_one({"user_id": ord_doc['user_id']}, {"$set": {"is_premium": True, "premium_until": until}}, upsert=True)

            await message.reply("✅ Pembayaran diterima. Terima kasih.")
        except Exception as e:
            logger.exception("confirm_pay error: %s", e)
            await message.reply(f"⚠️ Gagal memproses: {e}")

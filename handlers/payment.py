import datetime
from bson import ObjectId
from pyrogram import Client, filters
from database import orders_col, products_col, users_col  # pastikan sudah ada
from config import LOG_CHANNEL_ID, LOG_GROUP_ID  # optional kalau mau lewat config


async def send_log(app: Client, text: str):
    """Kirim log ke channel & ke grup owner"""
    try:
        await app.send_message(-1003242217013, text)  # LOG CHANNEL
    except:
        pass
    try:
        await app.send_message(-1003236389657, text)  # LOG GROUP
    except:
        pass


async def register_payment(app: Client):
    @app.on_message(filters.command("confirm"))
    async def confirm_payment(_, message):
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply("⚠️ Usage: /confirm <ORDER_ID>")

        oid = parts[1]

        # Harus reply foto
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Reply ke pesan yang berisi foto bukti pembayaran!")

        # Download foto
        fpath = await message.reply_to_message.download(
            file_name=f"uploads/proof_{message.from_user.id}_{oid}.jpg"
        )

        try:
            # Update order jadi paid & simpan bukti
            await orders_col.update_one(
                {"_id": ObjectId(oid)},
                {"$set": {
                    "payment_proof": fpath,
                    "status": "paid",
                    "paid_at": datetime.datetime.utcnow()
                }}
            )

            ord_doc = await orders_col.find_one({"_id": ObjectId(oid)})
            if not ord_doc:
                return await message.reply("❌ Order tidak ditemukan di database!")

            prod = await products_col.find_one({"_id": ObjectId(ord_doc["product_id"])})
            if not prod:
                return await message.reply("❌ Produk tidak ditemukan di database!")

            # Jika premium -> aktif 30 hari
            if "premium" in prod.get("name", "").lower():
                until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
                await users_col.update_one(
                    {"user_id": ord_doc["user_id"]},
                    {"$set": {"is_premium": True, "premium_until": until}},
                    upsert=True
                )

            # Reply ke user
            await message.reply("✅ Pembayaran diterima. Premium aktif 30 hari 🎉")

            # Kirim log
            log_text = f"""
✅ **PAYMENT CONFIRMED**
👤 User ID : `{message.from_user.id}`
🛒 Order ID : `{oid}`
📦 Produk : `{prod.get('name')}`
💎 Status : Premium 30 hari aktif
📎 Bukti : `{fpath}`
⏰ Waktu : `{datetime.datetime.utcnow()}` UTC
"""
            await send_log(app, log_text)

        except Exception as err:
            await message.reply(f"⚠️ Gagal memproses pembayaran.\nError: {err}")
            await send_log(app, f"❌ PAYMENT FAIL\nOrder: `{oid}`\nError: `{err}`")

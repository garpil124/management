import datetime
import os
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import Message

from database import orders_col, products_col, users_col  # sesuaikan jika beda import

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@Client.on_message(filters.command("confirm"))
async def confirm_payment(c: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("⚠️ Usage: reply foto bukti pembayaran dengan:\n/confirm <ORDER_ID>")

    oid = parts[1]

    # pastikan di-reply ke foto
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("❌ Harap reply ke foto bukti pembayaran!")

    # download foto payment proof
    fpath = await message.reply_to_message.download(
        file_name=f"{UPLOAD_DIR}/proof_{message.from_user.id}_{oid}.jpg"
    )

    try:
        # update order jadi paid
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
            return await message.reply("⚠️ Order tidak ditemukan di database!")

        prod = await products_col.find_one({"_id": ObjectId(ord_doc['product_id'])})
        if not prod:
            return await message.reply("⚠️ Produk pada order ini tidak ditemukan!")

        # jika produk premium, aktifkan 30 hari
        if 'premium' in prod.get('name', '').lower():
            until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            await users_col.update_one(
                {"user_id": ord_doc["user_id"]},
                {"$set": {"is_premium": True, "premium_until": until}},
                upsert=True
            )

        await message.reply("✅ Pembayaran berhasil dikonfirmasi!\n⭐ Premium aktif 30 hari.")

    except Exception as err:
        await message.reply(f"⚠️ Gagal memproses pembayaran.\nError:\n`{err}`")

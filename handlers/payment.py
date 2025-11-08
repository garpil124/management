from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from db.mongo import backups_col, products_col, users_col, partners_col  # sesuaikan jika perlu
from db.mongo import orders_col  # pastikan di mongo.py ada orders_col juga
from bson.objectid import ObjectId
import datetime
import os

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@Client.on_callback_query(filters.regex(r"^buy:"))
async def on_buy(client: Client, cq: CallbackQuery):
    pid = cq.data.split(":",1)[1]
    try:
        prod = await products_col.find_one({"_id": ObjectId(pid)})
    except:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)

    if not prod:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)

    order = {
        "user_id": cq.from_user.id,
        "product_id": pid,
        "amount": prod["price"],
        "status": "pending",
        "payment_proof": None,
        "created_at": datetime.datetime.utcnow()
    }

    res = await orders_col.insert_one(order)
    oid = str(res.inserted_id)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔷 QRIS (Upload Bukti)", callback_data=f"pay:upload:{oid}")],
        [InlineKeyboardButton("🏧 Dana / GoPay (Transfer)", callback_data=f"pay:transfer:{oid}")],
        [InlineKeyboardButton("❌ Batal", callback_data=f"pay:cancel:{oid}")]
    ])

    await cq.message.answer(
        f"📋 Order dibuat: <b>{prod['name']}</b>\nJumlah: Rp{prod['price']}\nOrder ID: <code>{oid}</code>",
        reply_markup=kb,
        parse_mode="html"
    )
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^pay:upload:"))
async def pay_upload_cb(client: Client, cq: CallbackQuery):
    _, _, oid = cq.data.split(":")
    await cq.message.answer(
        "Silahkan upload foto bukti pembayaran dengan **reply** ke pesan ini, lalu ketik:\n"
        f"`/confirm {oid}`",
        parse_mode="markdown"
    )
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^pay:transfer:"))
async def pay_transfer_cb(client: Client, cq: CallbackQuery):
    _, _, oid = cq.data.split(":")
    from config import PAYMENT_QRIS_DANA, PAYMENT_QRIS_GOPAY

    text = "Silahkan transfer ke salah satu:\n"
    if PAYMENT_QRIS_DANA:
        text += f"• Dana: {PAYMENT_QRIS_DANA}\n"
    if PAYMENT_QRIS_GOPAY:
        text += f"• GoPay: {PAYMENT_QRIS_GOPAY}\n"

    text += f"\nSetelah transfer, upload bukti dan ketik:\n`/confirm {oid}`"
    await cq.message.answer(text, parse_mode="markdown")
    await cq.answer()


@Client.on_message(filters.command("confirm") & filters.private)
async def confirm_payment(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("Format: reply foto → `/confirm <order_id>`", parse_mode="markdown")

        oid = args[1]

        # pastikan reply ke foto
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Harus reply ke foto bukti pembayaran!")

        # download file
        file_path = await message.reply_to_message.download(
            file_name=os.path.join(UPLOAD_FOLDER, f"proof_{message.from_user.id}_{oid}.jpg")
        )

        # update order jadi paid
        await orders_col.update_one(
            {"_id": ObjectId(oid)},
            {"$set": {"payment_proof": file_path, "status": "paid", "paid_at": datetime.datetime.utcnow()}}
        )

        order = await orders_col.find_one({"_id": ObjectId(oid)})
        if not order:
            return await message.reply("❌ Order tidak ditemukan!")

        prod = await products_col.find_one({"_id": ObjectId(order["product_id"])})
        if not prod:
            return await message.reply("❌ Produk order tidak ditemukan!")

        # jika premium -> aktif 30 hari
        if "premium" in prod.get("name", "").lower():
            until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            await users_col.update_one(
                {"user_id": order["user_id"]},
                {"$set": {"is_premium": True, "premium_until": until}},
                upsert=True
            )

        await message.reply("✅ Pembayaran diterima! Premium aktif 30 hari.")

    except Exception as e:
        await message.reply(f"⚠️ Gagal memproses pembayaran.\nError: `{e}`", parse_mode="markdown")

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from db.mongo import orders_col, products_col, users_col
from bson.objectid import ObjectId
import datetime

@Client.on_callback_query(filters.regex(r"^buy:"))
async def on_buy(client: Client, cq: CallbackQuery):
    pid = cq.data.split(":",1)[1]
    try:
        prod = await products_col.find_one({"_id": ObjectId(pid)})
    except:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)
    if not prod:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)

    # create order
    order = {
        "user_id": cq.from_user.id,
        "product_id": pid,
        "amount": prod['price'],
        "status": "pending",
        "payment_method": None,
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
    await cq.message.answer(f"📋 Order dibuat: <b>{prod['name']}</b>\nJumlah: Rp{prod['price']}\nOrder ID: <code>{oid}</code>", reply_markup=kb, parse_mode="html")
    await cq.answer()

@Client.on_callback_query(filters.regex(r"^pay:upload:"))
async def pay_upload_cb(client: Client, cq: CallbackQuery):
    _, _, oid = cq.data.split(":")
    await cq.message.answer("Silahkan upload foto bukti pembayaran sebagai balasan (reply) ke pesan ini, lalu gunakan /confirm <ORDER_ID> pada pesan balasan foto.")
    await cq.answer()

@Client.on_callback_query(filters.regex(r"^pay:transfer:"))
async def pay_transfer_cb(client: Client, cq: CallbackQuery):
    _, _, oid = cq.data.split(":")
    # show transfer details - owner must set PAYMENT_QRIS_* in config or .env
    from config import PAYMENT_QRIS_DANA, PAYMENT_QRIS_GOPAY
    text = "Silahkan transfer ke salah satu:\n"
    if PAYMENT_QRIS_DANA:
        text += f"• Dana: {PAYMENT_QRIS_DANA}\n"
    if PAYMENT_QRIS_GOPAY:
        text += f"• GoPay: {PAYMENT_QRIS_GOPAY}\n\nSetelah transfer, upload bukti dan gunakan /confirm {oid}"
    await cq.message.answer(text)
    await cq.answer()

@Client.on_message(filters.command("confirm") & filters.private)
async def confirm_payment(client: Client, message: Message):
    """
    User should reply to their uploaded photo with /confirm <order_id>
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply("Usage: reply to your photo with /confirm <ORDER_ID>")

        oid = parts[1]
        # get replied message
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Reply ke pesan yang berisi foto bukti pembayaran.")

        # download photo
        fpath = await message.reply_to_message.download(file_name=f"uploads/proof_{message.from_user.id}_{oid}.jpg")
        # update order
        await orders_col.update_one({"_id": ObjectId(oid)}, {"$set": {"payment_proof": fpath, "status": "paid", "paid_at": datetime.datetime.utcnow()}})
        # give premium if product is premium (optional logic)
        ord_doc = await orders_col.find_one({"_id": ObjectId(oid)})
        prod = await products_col.find_one({"_id": ObjectId(ord_doc['product_id'])})
        # if product name contains 'premium' then give premium
        if 'premium' in prod.get('name','').lower():
            until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            await users_col.update_one({"user_id": ord_doc['user_id']}, {"$set": {"is_premium": True, "premium_until": until}}, upsert=True)

await message.reply("✅ Pembayaran diterima. Premium aktif 30 hari.")
        else:
            await message.reply("✅ Pembayaran diterima. Terima kasih.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

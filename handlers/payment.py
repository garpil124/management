import os, datetime
from bson import ObjectId
from bot import app
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.mongo import orders_col, products_col, users_col, payments_col
from utils.helpers import send_log_all, safe_send

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_callback_query(filters.regex(r"^buy:"))
async def on_buy(client, cq: CallbackQuery):
    pid = cq.data.split(":",1)[1]
    try:
        prod = await products_col.find_one({"_id": ObjectId(pid)}) if hasattr(products_col, "find_one") else products_col.find_one({"_id": pid})
    except Exception:
        prod = None
    if not prod:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)

    order = {
        "user_id": cq.from_user.id,
        "product_id": str(prod.get("_id") if prod.get("_id") else pid),
        "amount": prod.get("price", 0),
        "status": "pending",
        "payment_proof": None,
        "created_at": datetime.datetime.utcnow()
    }
    # insert (motor async or pymongo sync)
    if getattr(orders_col, "insert_one", None) and asyncio.iscoroutinefunction(orders_col.insert_one):
        res = await orders_col.insert_one(order)
        oid = str(res.inserted_id)
    else:
        # sync insert
        res = orders_col.insert_one(order)
        oid = str(res.inserted_id)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔷 Upload Bukti (QRIS)", callback_data=f"pay:upload:{oid}")],
        [InlineKeyboardButton("🏧 Transfer (Dana/GoPay)", callback_data=f"pay:transfer:{oid}")],
        [InlineKeyboardButton("❌ Batal", callback_data=f"pay:cancel:{oid}")]
    ])

    await cq.message.answer(
        f"📋 Order dibuat: <b>{prod.get('name')}</b>\nJumlah: Rp{prod.get('price')}\nOrder ID: <code>{oid}</code>",
        reply_markup=kb,
        parse_mode="html"
    )
    await send_log_all(client, f"🆕 ORDER — user={cq.from_user.id} order={oid} prod={prod.get('name')}")
    await cq.answer()


@app.on_callback_query(filters.regex(r"^pay:upload:"))
async def pay_upload_cb(client, cq: CallbackQuery):
    _, _, oid = cq.data.split(":")
    await cq.message.answer(f"Silakan upload foto bukti dan reply ke foto lalu ketik /confirm {oid}", parse_mode="markdown")
    await cq.answer()


@app.on_message(filters.command("confirm") & filters.private)
async def confirm_payment(client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply("⚠️ Usage (reply foto) -> /confirm <ORDER_ID>")
        oid = parts[1]
        # check reply photo
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Reply ke foto bukti pembayaran.")
        # download
        fpath = await message.reply_to_message.download(file_name=os.path.join(UPLOAD_DIR, f"proof_{message.from_user.id}_{oid}.jpg"))

# update order -> support motor/pymongo
        if getattr(orders_col, "update_one", None) and asyncio.iscoroutinefunction(orders_col.update_one):
            await orders_col.update_one({"_id": ObjectId(oid)}, {"$set": {"payment_proof": fpath, "status": "paid", "paid_at": datetime.datetime.utcnow()}})
            ord_doc = await orders_col.find_one({"_id": ObjectId(oid)})
        else:
            orders_col.update_one({"_id": ObjectId(oid)}, {"$set": {"payment_proof": fpath, "status": "paid", "paid_at": datetime.datetime.utcnow()}})
            ord_doc = orders_col.find_one({"_id": ObjectId(oid)})

        if not ord_doc:
            return await message.reply("❌ Order tidak ditemukan setelah update.")
        # product
        prod = products_col.find_one({"_id": ObjectId(ord_doc.get("product_id"))}) if not asyncio.iscoroutinefunction(products_col.find_one) else await products_col.find_one({"_id": ObjectId(ord_doc.get("product_id"))})

if not prod:
            return await message.reply("❌ Produk tidak ditemukan.")
        # premium check
        if "premium" in prod.get("name","").lower():
            until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            if getattr(users_col, "update_one", None) and asyncio.iscoroutinefunction(users_col.update_one):
                await users_col.update_one({"user_id": ord_doc.get("user_id")}, {"$set": {"is_premium": True, "premium_until": until}}, upsert=True)
            else:
                users_col.update_one({"user_id": ord_doc.get("user_id")}, {"$set": {"is_premium": True, "premium_until": until}}, upsert=True)

        try:

              await message.reply(f"✅ Pembayaran diterima.\nPremium aktif {prod.get('name')} selama 30 hari.")
                    users_col.update_one(
          {"user_id": order_doc.get("user_id")},
          {"$set": {"is_premium": True, "premium_until": until}}
    )

    await send_log_all(Client, f"✅ PAYMENT SUCCESS!\nUser: {order_doc.get('user_id')}\nProduct: {prod.get('name')}")

   except Exception as err:
     await message.reply(f"❌ ERROR memproses pembayaran. ({err})")
     await send_log_all(Client, f"❌ ERROR /confirm: {err}")

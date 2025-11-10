import os, datetime, asyncio
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
    except:
        prod = None

    if not prod:
        return await cq.answer("Produk tidak ditemukan", show_alert=True)

    order = {
        "user_id": cq.from_user.id,
        "product_id": str(prod.get("_id")),
        "amount": prod.get("price", 0),
        "status": "pending",
        "payment_proof": None,
        "created_at": datetime.datetime.utcnow()
    }

    if asyncio.iscoroutinefunction(orders_col.insert_one):
        res = await orders_col.insert_one(order)
    else:
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

        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Reply ke foto bukti pembayaran.")

        fpath = await message.reply_to_message.download(
            file_name=os.path.join(UPLOAD_DIR, f"proof_{message.from_user.id}_{oid}.jpg")
        )

        # Update order to PAID
        if asyncio.iscoroutinefunction(orders_col.update_one):
            await orders_col.update_one(
                {"_id": ObjectId(oid)},
                {"$set": {"payment_proof": fpath, "status": "paid", "paid_at": datetime.datetime.utcnow()}}
            )
            ord_doc = await orders_col.find_one({"_id": ObjectId(oid)})
        else:
            orders_col.update_one(
                {"_id": ObjectId(oid)},
                {"$set": {"payment_proof": fpath, "status": "paid", "paid_at": datetime.datetime.utcnow()}}
            )
            ord_doc = orders_col.find_one({"_id": ObjectId(oid)})

        if not ord_doc:
            return await message.reply("❌ Order tidak ditemukan setelah update.")

        # Ambil product
        if asyncio.iscoroutinefunction(products_col.find_one):
            prod = await products_col.find_one({"_id": ObjectId(ord_doc.get("product_id"))})
        else:
            prod = products_col.find_one({"_id": ObjectId(ord_doc.get("product_id"))})

        if not prod:
            return await message.reply("❌ Produk tidak ditemukan.")

        # Cek premium
        if "premium" in prod.get("name","").lower():
            until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            if asyncio.iscoroutinefunction(users_col.update_one):
                await users_col.update_one(
                    {"user_id": ord_doc.get("user_id")},
                    {"$set": {"is_premium": True, "premium_until": until}},
                    upsert=True
                )
            else:
                users_col.update_one(
                    {"user_id": ord_doc.get("user_id")},
                    {"$set": {"is_premium": True, "premium_until": until}},
                    upsert=True
                )

        await message.reply(f"✅ Pembayaran berhasil!\nPremium aktif: {prod.get('name')} selama 30 hari.")
        await send_log_all(client, f"✅ PAYMENT SUCCESS\nUser: {ord_doc.get('user_id')}\nProduct: {prod.get('name')}")

    except Exception as err:
        await message.reply(f"❌ ERROR memproses pembayaran.\n{err}")
        await send_log_all(client, f"❌ ERROR /confirm: {err}")

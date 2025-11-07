import os
import datetime
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.mongo import payments_col, products_col, users_col
from config import OWNER_ID, LOG_CHAT_ID
from utils.helpers import send_log

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def register_payment(app: Client):

    # ─────────────────────────────────
    # ✅ ADMIN: Set QR
    # /setqr dana <reply photo>
    # /setqr gopay <reply photo>
    # ─────────────────────────────────
    @app.on_message(filters.command("setqr") & filters.user(OWNER_ID))
    async def set_qr(client, message):
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Reply ke gambar QR nya.")

        args = message.text.split()
        if len(args) < 2:
            return await message.reply("Format: /setqr <dana|gopay>")

        payment_name = args[1].lower()
        if payment_name not in ["dana", "gopay"]:
            return await message.reply("❌ Hanya dana / gopay.")

        file_path = await message.reply_to_message.download(
            file_name=os.path.join(UPLOAD_FOLDER, f"qr_{payment_name}.jpg")
        )

        await payments_col.update_one(
            {"name": payment_name},
            {"$set": {"qr_path": file_path, "updated_at": datetime.datetime.utcnow()}},
            upsert=True
        )

        await message.reply(f"✅ QR {payment_name.upper()} berhasil disimpan!")

    # ─────────────────────────────────
    # ✅ USER: Beli Produk
    # /buy <product_id>
    # ─────────────────────────────────
    @app.on_message(filters.command("buy"))
    async def buy_product(client, message):
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("Format: /buy <product_id>")

        pid = args[1]
        prod = await products_col.find_one({"_id": ObjectId(pid)})

        if not prod:
            return await message.reply("❌ Produk tidak ditemukan.")

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Dana", callback_data=f"pay_dana_{pid}")],
            [InlineKeyboardButton("💰 Gopay", callback_data=f"pay_gopay_{pid}")]
        ])

        await message.reply(
            f"🛒 **{prod['name']}**\n💵 Harga: {prod['price']}\n\nPilih metode bayar:",
            reply_markup=kb
        )

    # ─────────────────────────────────
    # ✅ CALLBACK: Pilih Metode
    # ─────────────────────────────────
    @app.on_callback_query(filters.regex("^pay_(dana|gopay)_(.*)"))
    async def pay_cb(client, callback):
        method, pid = callback.data.split("_")[1], callback.data.split("_")[2]
        pm = await payments_col.find_one({"name": method})

        if not pm or "qr_path" not in pm:
            return await callback.answer("❌ QR belum diset admin!", show_alert=True)

        prod = await products_col.find_one({"_id": ObjectId(pid)})
        if not prod:
            return await callback.answer("❌ Produk hilang!", show_alert=True)

        order = {
            "user_id": callback.from_user.id,
            "product_id": ObjectId(pid),
            "price": prod["price"],
            "method": method,
            "status": "waiting_payment",
            "created_at": datetime.datetime.utcnow()
        }

        ins = await payments_col.insert_one(order)

        caption = (
            f"📌 **Order ID:** `{ins.inserted_id}`\n"
            f"📦 Produk: {prod['name']}\n"
            f"💵 Harga: {prod['price']}\n"
            f"🏦 Metode: {method.upper()}\n\n"
            f"📸 Silakan transfer lalu kirim bukti foto dengan reply:\n"
            f"`/confirm {ins.inserted_id}`"
        )

        await client.send_photo(
            chat_id=callback.message.chat.id,
            photo=pm["qr_path"],
            caption=caption
        )

        await callback.answer()

    # ─────────────────────────────────
    # ✅ USER: Upload bukti bayar
    # reply foto +:  /confirm <order_id>
    # ─────────────────────────────────
    @app.on_message(filters.command("confirm"))
    async def confirm_pay(client, message):
        try:
            args = message.text.split()
            if len(args) < 2:
                return await message.reply("Format: reply foto → /confirm <order_id>")

            oid = args[1]

            if not message.reply_to_message or not message.reply_to_message.photo:
                return await message.reply("❌ Reply ke foto bukti pembayaran.")

            file_path = await message.reply_to_message.download(
                file_name=os.path.join(UPLOAD_FOLDER, f"proof_{message.from_user.id}_{oid}.jpg")
            )

            await payments_col.update_one(
                {"_id": ObjectId(oid)},
                {"$set": {"proof": file_path, "status": "paid", "paid_at": datetime.datetime.utcnow()}}
            )

            order = await payments_col.find_one({"_id": ObjectId(oid)})
            prod  = await products_col.find_one({"_id": ObjectId(order["product_id"])})

            # Kalau produk premium -> kasih akses 30 hari
            if "premium" in prod.get("name", "").lower():
                until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
                await users_col.update_one(
                    {"user_id": order["user_id"]},
                    {"$set": {"is_premium": True, "premium_until": until}},
                    upsert=True
                )

            try:
                await message.reply("✅ Pembayaran diterima. Premium aktif 30 hari!")
            except:
                pass

            # Kirim log ke owner
            await send_log(
                client,
                LOG_CHAT_ID,
                f"💰 *Pembayaran masuk*\nUser: {order['user_id']}\nProduct: {prod['name']}\nOrder: `{oid}`"
            )

        except Exception as err:
            await message.reply(f"⚠️ Gagal memproses pembayaran:\n`{err}`")

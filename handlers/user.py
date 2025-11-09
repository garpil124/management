from pyrogram import Client, filters from pyrogram.types import ( Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton ) import asyncio import logging import os from datetime import datetime, timedelta

Local helpers (to avoid depending on other utils)

logger = logging.getLogger("handlers.user")

DB collections will be imported lazily inside register to avoid import cycles

Helper to detect async Motor collection vs sync pymongo

async def _is_async_col(col): return asyncio.iscoroutinefunction(getattr(col, "find_one", None))

Escape for HTML (simple)

def esc_html(text: str) -> str: if text is None: return "" return (str(text) .replace("&", "&") .replace("<", "<") .replace(">", ">") )

Default invoice expiry minutes

INVOICE_EXP_MIN = 60  # 1 hour

Register function expected by main.py

def register_user(app: Client): # lazy imports (so main can import handlers safely) try: from db.mongo import products_col, orders_col, users_col except Exception: products_col = None orders_col = None users_col = None

# ---------- START handler (compact) ----------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    uname = user.first_name if user else "User"
    # simple main menu — other handlers will respond to callbacks
    text = (
        f"👋 Halo {esc_html(uname)}\n"
        "🤖 GARFIELD STORE\n"
        "📌 Silakan pilih menu di bawah :"
    )
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍 Produk", callback_data="menu_product")],
            [InlineKeyboardButton("📘 Bantuan", callback_data="menu_help")],
            [InlineKeyboardButton("👥 Support", url="https://t.me/storegarf")]
        ]
    )
    await message.reply(text, reply_markup=kb)

# ---------- product listing via callback ----------
@app.on_callback_query(filters.regex(r"^menu_product$"))
async def cb_menu_product(client: Client, callback: CallbackQuery):
    try:
        # load products (show public or owned by partner?) — we show all available
        if products_col is None:
            await callback.answer("Produk tidak tersedia (DB belum diatur)", show_alert=True)
            return

        # handle motor vs pymongo
        if asyncio.iscoroutinefunction(getattr(products_col, "find", None)):
            cursor = products_col.find({"stock": {"$gt": 0}}).sort("created_at", -1)
            data = [p async for p in cursor]
        else:
            data = list(products_col.find({"stock": {"$gt": 0}}).sort("created_at", -1))

        if not data:
            try:
                await callback.message.edit_text("📦 Belum ada produk tersedia.")
            except Exception:
                pass
            await callback.answer()
            return

        # build buttons — show up to 25
        buttons = []
        for p in data[:25]:
            label = f"{p.get('name')} — Rp{p.get('price')}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"product_{p.get('code')}")])

        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")])

        await callback.message.edit_text("📦 Pilih produk:", reply_markup=InlineKeyboardMarkup(buttons))
        await callback.answer()

    except Exception as e:
        logger.exception("menu_product error: %s", e)
        await callback.answer("Gagal memuat produk", show_alert=True)

# ---------- show product detail ----------
@app.on_callback_query(filters.regex(r"^product_"))
async def cb_show_product(client: Client, callback: CallbackQuery):
    try:
        code = callback.data.split("_", 1)[1]
        if products_col is None:
            return await callback.answer("Produk tidak tersedia (DB).", show_alert=True)

        # find product doc
        if asyncio.iscoroutinefunction(getattr(products_col, 'find_one', None)):
            prod = await products_col.find_one({"code": code})
        else:
            prod = products_col.find_one({"code": code})

        if not prod:
            return await callback.answer("Produk tidak ditemukan.", show_alert=True)

        # build text
        text = (
            f"🧾 <b>Detail Produk</b>\n\n"
            f"📌 <b>{esc_html(prod.get('name'))}</b>\n"
            f"💳 Harga: Rp{esc_html(prod.get('price'))}\n"
            f"🆔 Kode: <code>{esc_html(prod.get('code'))}</code>\n\n"
            f"{esc_html(prod.get('desc', '-'))}"
        )

        # buttons: buy + back
        buttons = [
            [InlineKeyboardButton("💳 Beli", callback_data=f"buy_{prod.get('_id') or prod.get('code')}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_product")]
        ]

        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await callback.answer()

    except Exception as e:
        logger.exception("show_product error: %s", e)
        await callback.answer("Gagal memuat detail produk", show_alert=True)

# ---------- buy flow (create order + invoice) ----------
@app.on_callback_query(filters.regex(r"^buy_"))
async def cb_buy_product(client: Client, callback: CallbackQuery):
    try:
        ident = callback.data.split("_", 1)[1]
        # try lookup by ObjectId-like or by code
        if products_col is None or orders_col is None:
            return await callback.answer("Fungsi beli belum tersedia (DB).", show_alert=True)

        # find product
        if asyncio.iscoroutinefunction(getattr(products_col, 'find_one', None)):
            prod = await products_col.find_one({"_id": ident}) or await products_col.find_one({"code": ident})
        else:
            prod = products_col.find_one({"_id": ident}) or products_col.find_one({"code": ident})

        if not prod:
            return await callback.answer("Produk tidak ditemukan.", show_alert=True)

        # check stock
        stock = prod.get('stock', 1)
        if stock <= 0:
            return await callback.answer("Produk habis.", show_alert=True)

        # create order
        order = {
            "user_id": callback.from_user.id,
            "product_id": str(prod.get('_id') or prod.get('code')),
            "product_name": prod.get('name'),
            "amount": prod.get('price'),
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=INVOICE_EXP_MIN),
        }

        if asyncio.iscoroutinefunction(getattr(orders_col, 'insert_one', None)):
            res = await orders_col.insert_one(order)
            oid = str(res.inserted_id)
        else:
            res = orders_col.insert_one(order)
            oid = str(res.inserted_id)

        # invoice buttons
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔷 Bayar via QR (upload bukti)", callback_data=f"pay_upload_{oid}")],
            [InlineKeyboardButton("❌ Batal", callback_data=f"pay_cancel_{oid}")]
        ])

        await callback.message.edit_text(
            f"🧾 Order dibuat\nOrder ID: <code>{oid}</code>\nProduk: <b>{esc_html(prod.get('name'))}</b>\nJumlah: Rp{esc_html(prod.get('price'))}\n\nInvoice berlaku {INVOICE_EXP_MIN} menit.",
            reply_markup=kb
        )

        # notify owner/log (if product has owner_id and owner's log_group stored)
        owner_id = prod.get('owner_id')
        log_group = prod.get('log_group')
        try:
            if log_group:
                await client.send_message(log_group, f"🆕 Order: {oid}\nUser: {callback.from_user.id}\nProduk: {prod.get('name')}\nJumlah: Rp{prod.get('price')}")
        except Exception:
            pass

        await callback.answer("Order dibuat. Lakukan pembayaran dan upload bukti.")

    except Exception as e:
        logger.exception("cb_buy_product: %s", e)
        await callback.answer("Gagal membuat order", show_alert=True)

# ---------- pay upload handler (user will upload photo and then /confirm <orderid>) ----------
@app.on_callback_query(filters.regex(r"^pay_upload_(.+)"))
async def cb_pay_upload(client: Client, callback: CallbackQuery):
    try:
        oid = callback.data.split("pay_upload_")[1]
        await callback.message.edit_text(
            f"Silakan upload bukti pembayaran dan reply foto tersebut kemudian ketik /confirm {oid}"
        )
        await callback.answer()
    except Exception as e:
        logger.exception("cb_pay_upload: %s", e)
        await callback.answer("Gagal", show_alert=True)

@app.on_callback_query(filters.regex(r"^pay_cancel_(.+)"))
async def cb_pay_cancel(client: Client, callback: CallbackQuery):
    try:
        oid = callback.data.split("pay_cancel_")[1]
        # set order canceled
        if asyncio.iscoroutinefunction(getattr(orders_col, 'update_one', None)):
            await orders_col.update_one({"_id": oid}, {"$set": {"status": "canceled"}})
        else:
            orders_col.update_one({"_id": oid}, {"$set": {"status": "canceled"}})
        await callback.message.edit_text("❌ Order dibatalkan.")
        await callback.answer()
    except Exception as e:
        logger.exception("cb_pay_cancel: %s", e)
        await callback.answer("Gagal membatalkan", show_alert=True)

# ---------- confirm command (user replies image then runs /confirm <orderid>) ----------
@app.on_message(filters.command("confirm") & filters.private)
async def cmd_confirm(client: Client, message: Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return await message.reply("⚠️ Format: reply foto bukti lalu ketik /confirm <ORDER_ID>")

        oid = parts[1]
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply("❌ Reply ke foto bukti pembayaran")

        # download photo
        path = await message.reply_to_message.download()

        # load order
        if asyncio.iscoroutinefunction(getattr(orders_col, 'find_one', None)):
            ord_doc = await orders_col.find_one({"_id": oid})
        else:
            ord_doc = orders_col.find_one({"_id": oid})

        if not ord_doc:
            return await message.reply("❌ Order tidak ditemukan.")

        # check expiry
        expires_at = ord_doc.get('expires_at')
        if isinstance(expires_at, datetime):
            if datetime.utcnow() > expires_at:
                # mark expired
                try:
                    if asyncio.iscoroutinefunction(getattr(orders_col, 'update_one', None)):
                        await orders_col.update_one({"_id": oid}, {"$set": {"status": "expired"}})
                    else:
                        orders_col.update_one({"_id": oid}, {"$set": {"status": "expired"}})
                except Exception:
                    pass
                return await message.reply("❌ Invoice sudah kadaluarsa.")

        # update order: set paid
        if asyncio.iscoroutinefunction(getattr(orders_col, 'update_one', None)):
            await orders_col.update_one({"_id": oid}, {"$set": {"status": "paid", "payment_proof": path, "paid_at": datetime.utcnow()}})
            ord_doc = await orders_col.find_one({"_id": oid})
        else:
            orders_col.update_one({"_id": oid}, {"$set": {"status": "paid", "payment_proof": path, "paid_at": datetime.utcnow()}})
            ord_doc = orders_col.find_one({"_id": oid})

        # reduce stock (best-effort)
        pid = ord_doc.get('product_id')
        try:
            if asyncio.iscoroutinefunction(getattr(products_col, 'update_one', None)):
                await products_col.update_one({"_id": pid}, {"$inc": {"stock": -1}})
            else:
                products_col.update_one({"_id": pid}, {"$inc": {"stock": -1}})
        except Exception:
            pass

        # deliver file if product has file_id or file_path
        try:
            prod = None
            if asyncio.iscoroutinefunction(getattr(products_col, 'find_one', None)):
                prod = await products_col.find_one({"_id": pid})
            else:
                prod = products_col.find_one({"_id": pid})

            if prod:
                # if product has file_id (file_stored on telegram) send by file_id
                if prod.get('file_id'):
                    await client.send_document(message.from_user.id, prod.get('file_id'))
                elif prod.get('file_path') and os.path.exists(prod.get('file_path')):
                    await client.send_document(message.from_user.id, prod.get('file_path'))
                else:
                    await client.send_message(message.from_user.id, "✅ Pembayaran diterima. File/produk akan dikirim manual oleh penjual.")

        except Exception as e:
            logger.exception("delivery error: %s", e)

        # notify owner/log group if present
        try:
            if prod and prod.get('log_group'):
                await client.send_message(prod.get('log_group'), f"✅ Pembayaran diterima\nOrder: {oid}\nUser: {message.from_user.id}\nProduk: {prod.get('name')}")
        except Exception:
            pass

        await message.reply("✅ Pembayaran tercatat. Terima kasih!")

    except Exception as e:
        logger.exception("confirm error: %s", e)
        await message.reply(f"⚠️ Gagal memproses konfirmasi: {e}")

# ---------- background: cleanup expired invoices (best-effort) ----------
async def _cleanup_expired():
    # run periodically
    while True:
        try:
            if orders_col is None:
                await asyncio.sleep(60)
                continue
            now = datetime.utcnow()
            if asyncio.iscoroutinefunction(getattr(orders_col, 'update_many', None)):
                await orders_col.update_many({"status": "pending", "expires_at": {"$lte": now}}, {"$set": {"status": "expired"}})
            else:
                orders_col.update_many({"status": "pending", "expires_at": {"$lte": now}}, {"$set": {"status": "expired"}})
        except Exception:
            pass
        await asyncio.sleep(60)  # run every minute

# Start cleanup task when client starts
async def _on_start(_):
    try:
        app.loop.create_task(_cleanup_expired())
    except Exception:
        # fallback to ensure not crashing
        asyncio.create_task(_cleanup_expired())

# register startup hook
try:
    app.add_handler = getattr(app, 'add_handler', None)  # no-op, just check
except Exception:
    pass

# Pyrogram doesn't provide a direct "on_start" hook here, but we can attach to "on_message" first call or rely on main to start tasks.
# Best-effort: schedule cleanup when client is running
try:
    # if app has "idle" event later, we still call _on_start now but it will schedule cleanup when loop is running
    asyncio.get_event_loop().call_soon_threadsafe(lambda: asyncio.create_task(_cleanup_expired()))
except Exception:
    # ignore if not able to schedule now
    pass

logger.info("✅ handlers/user.py registered")

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.mongo import products_col
from datetime import datetime


def register_product(app: Client):

    # ────────────────────────────────────────────────
    # COMMAND /produk (user mengetik manual)
    # ────────────────────────────────────────────────
    @app.on_message(filters.command("produk") & filters.private)
    async def cmd_produk(client: Client, message: Message):

        data = list(products_col.find().sort("created_at", -1).limit(50))

        # → kalau produk kosong
        if not data:
            await message.reply(
                "📦 Belum ada produk tersedia.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]]
                )
            )
            return

        teks = "<b>📦 Daftar Produk</b>\n\n"
        for p in data:
            teks += (
                f"• <b>{p['name']}</b>\n"
                f"  💰 Rp{p['price']}\n"
                f"  🆔 <code>{p['code']}</code>\n\n"
            )

        await message.reply(
            teks,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]]
            )
        )

    # ────────────────────────────────────────────────
    # CALLBACK BUTTON: tombol "📦 Produk" di menu start
    # ────────────────────────────────────────────────
    @app.on_callback_query(filters.regex("^menu_produk$"))
    async def cb_menu_produk(client: Client, callback: CallbackQuery):

        data = list(products_col.find().sort("created_at", -1).limit(50))

        # → Kalau produk masih kosong
        if not data:
            await callback.message.edit_text(
                "📦 Belum ada produk tersedia.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]]
                )
            )
            return

        teks = "<b>📦 Daftar Produk</b>\n\n"
        for p in data:
            teks += (
                f"• <b>{p['name']}</b>\n"
                f"  💰 Rp{p['price']}\n"
                f"  🆔 <code>{p['code']}</code>\n\n"
            )

        await callback.message.edit_text(
            teks,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Tambah Produk", callback_data="add_product")]]
            )
        )
        await callback.answer()

    # ────────────────────────────────────────────────
    # CALLBACK: tambah produk (owner only)
    # ────────────────────────────────────────────────
    @app.on_callback_query(filters.regex("^add_product$"))
    async def cb_add_product(client: Client, callback: CallbackQuery):

        await callback.message.edit_text(
            "🆕 <b>Tambah Produk Baru</b>\n\n"
            "Format kirim data seperti ini:\n"
            "<code>nama_produk | harga | kode</code>\n\n"
            "Contoh:\n"
            "<code>Premium 30 Hari | 15000 | P30</code>",
            parse_mode="html"
        )

        app.add_handler(waiting_product_handler)


# ────────────────────────────────────────────────────────────────
# Handler untuk menerima input data produk setelah user klik ADD
# ────────────────────────────────────────────────────────────────

async def waiting_product_handler(client: Client, message: Message):

    try:
        name, price, code = [x.strip() for x in message.text.split("|")]
    except:
        await message.reply("❌ Format salah. Gunakan format:\nNama | Harga | Kode", parse_mode="markdown")
        return

    products_col.insert_one({
        "name": name,
        "price": int(price),
        "code": code,
        "created_at": datetime.now()
    })

await message.reply(
        f"✅ Produk berhasil ditambahkan!\n\n"
        f"• <b>{name}</b>\n"
        f"💰 Rp{price}\n"
        f"🆔 <code>{code}</code>",
        parse_mode="html"
    )

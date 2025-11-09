from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.mongo import db

products = db.products
users = db.users

# === KEYBOARD MAIN MENU USER ===
def user_main():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍 Produk", callback_data="user:product_list"),
            InlineKeyboardButton("💳 Payment", callback_data="user:payment")
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="user:premium"),
            InlineKeyboardButton("📘 Bantuan", callback_data="user:help")
        ],
        [InlineKeyboardButton("👥 Support", url="https://t.me/storegarf")],
    ])

# === KEYBOARD PAYMENT ===
def payment_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 QRIS", callback_data="pay:qris")],
        [InlineKeyboardButton("💳 DANA", callback_data="pay:dana")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu:back")]
    ])

# === PREMIUM INFO KEYBOARD ===
def premium_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Beli Premium", callback_data="pay:qris")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu:back")]
    ])

# === GENERATE LIST PRODUCT BUTTON ===
async def product_buttons():
    btn = []
    async for p in products.find():
        btn.append([InlineKeyboardButton(p["name"], callback_data=f"user:product:{p['_id']}")])

    btn.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu:back")])
    return InlineKeyboardMarkup(btn)

# ===================== callback handler =====================

@Client.on_callback_query(filters.regex("^user:|^pay:|^menu:"))
async def user_callback(client: Client, cb: CallbackQuery):

    data = cb.data

    # ==== LIST PRODUK ====
    if data == "user:product_list":
        await cb.message.edit_text("🛍 *Daftar Produk Tersedia:*", reply_markup=await product_buttons())

    # ==== DETAIL PRODUK ====
    elif data.startswith("user:product:"):
        pid = data.split(":")[2]
        product = await products.find_one({"_id": pid})

        if not product:
            return await cb.answer("❌ Produk tidak ditemukan!", True)

        text = (
            f"🛍 **{product['name']}**\n"
            f"💰 Harga: Rp {product['price']}\n"
            f"📌 Deskripsi:\n{product['desc']}"
        )

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Beli", callback_data=f"pay:product:{pid}")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="user:product_list")]
        ])

        await cb.message.edit_text(text, reply_markup=btn)

    # ==== PAYMENT MENU ====
    elif data == "user:payment":
        await cb.message.edit_text("💳 Pilih metode pembayaran:", reply_markup=payment_kb())

    # ==== PREMIUM MENU ====
    elif data == "user:premium":
        await cb.message.edit_text(
            "⭐ *Keuntungan Premium*\n\n"
            "✅ Akses semua fitur\n"
            "⚡ Respon lebih cepat\n"
            "📌 Support prioritas\n"
            "⏳ Durasi: 30 Hari\n\n"
            "Harga: Rp XX.XXX",
            reply_markup=premium_kb()
        )

    # ==== BANTUAN ====
    elif data == "user:help":
        await cb.message.edit_text(
            "📘 *Bantuan Penggunaan*\n\n"
            "• Klik produk untuk detail\n"
            "• Klik beli untuk payment\n"
            "• Kirim bukti transaksi jika sudah bayar\n\n"
            "Butuh bantuan? Klik support",
            reply_markup=user_main()
        )

    # ==== BACK KE MENU UTAMA ====
    elif data == "menu:back":
        await cb.message.edit_text("🔙 *Kembali ke menu utama*", reply_markup=user_main())

    # ==== PAYMENT PROCESS ====
    elif data.startswith("pay:"):
        await cb.message.edit_text(
            "📸 Silahkan kirim bukti pembayaran (Screenshot/Foto)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Batal", callback_data="menu:back")]
            ])
        )

    await cb.answer()

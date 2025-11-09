from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.mongo import db

subowners = db.subowners  # Collection khusus sub-owner

# === KEYBOARD PANEL SUB-OWNER ===
def subowner_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 List Produk", callback_data="subowner:list_product")],
        [InlineKeyboardButton("📊 Cek Statistik", callback_data="subowner:stats")],
        [InlineKeyboardButton("👤 Profil Sub-Owner", callback_data="subowner:profile")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu:back")]
    ])

# === CEK APA USER SUB-OWNER ATAU BUKAN ===
async def is_subowner(user_id):
    return bool(await subowners.find_one({"user_id": user_id}))

@Client.on_callback_query(filters.regex("^subowner:"))
async def subowner_callback(client: Client, cb: CallbackQuery):

    user_id = cb.from_user.id

    # ❗ Jika bukan sub-owner, tolak akses
    if not await is_subowner(user_id):
        return await cb.answer("⛔ Kamu bukan sub-owner!", show_alert=True)

    data = cb.data.split(":")[1]

    # 🛍 List Produk (Placeholder dulu)
    if data == "list_product":
        await cb.message.edit_text(
            "🛍 *Daftar Produk:* \n\n(soon bakal keambil dari database)",
            reply_markup=subowner_kb()
        )

    # 📊 Statistik (Placeholder)
    elif data == "stats":
        await cb.message.edit_text(
            "📊 *Statistik Bot:* \n\nTotal User: -\nPremium: -\nProduk: -",
            reply_markup=subowner_kb()
        )

    # 👤 Profil Sub-Owner
    elif data == "profile":
        user = await subowners.find_one({"user_id": user_id})
        if user:
            await cb.message.edit_text(
                f"👤 **Profil Sub-Owner**\n\n"
                f"ID: `{user['user_id']}`\n"
                f"Username: @{user.get('username', '-')}\n"
                f"Aktif Sampai: `{user.get('expired', 'Unlimited')}`",
                reply_markup=subowner_kb()
            )
        else:
            await cb.message.edit_text("❌ Data sub-owner tidak ditemukan!", reply_markup=subowner_kb())

    await cb.answer()

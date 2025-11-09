from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from db.mongo import subowners_col, users_col, products_col  # pastikan collection ini ada
from datetime import datetime

# ================= KEYBOARDS ================= #

def owner_panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="owner:broadcast")],
        [InlineKeyboardButton("🧠 List User", callback_data="owner:list_user")],
        [InlineKeyboardButton("👥 List Sub-Owner", callback_data="owner:list_sub")],
        [InlineKeyboardButton("➕ Add Sub-Owner", callback_data="owner:add_sub")],
        [InlineKeyboardButton("⭐ List Premium", callback_data="owner:list_premium")],
        [InlineKeyboardButton("🛍 Kelola Produk", callback_data="owner:menu_produk")],
        [InlineKeyboardButton("📊 Statistik Bot", callback_data="owner:statistic")],
        [InlineKeyboardButton("⚙ Setting Bot Owner", callback_data="owner:setting")],
        [InlineKeyboardButton("🔻 Shutdown / Restart Bot", callback_data="owner:shutdown")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu:back")]
    ])

def produk_owner_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Tambah Produk", callback_data="owner:add_product")],
        [InlineKeyboardButton("📝 Edit Produk", callback_data="owner:edit_product")],
        [InlineKeyboardButton("🗑 Hapus Produk", callback_data="owner:del_product")],
        [InlineKeyboardButton("📃 List Produk", callback_data="owner:list_product")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner:back_panel")]
    ])

# ================= CALLBACK HANDLER ================= #

@Client.on_callback_query(filters.regex("^owner:"))
async def owner_callback(client: Client, cb: CallbackQuery):

    if cb.from_user.id != OWNER_ID:
        return await cb.answer("⛔ Bukan akses kamu!", show_alert=True)

    data = cb.data

    # PANEL UTAMA OWNER
    if data == "owner:panel":
        await cb.message.edit_text(
            "👑 **OWNER PANEL**\n────────────────",
            reply_markup=owner_panel_kb()
        )

    # LIST SUB OWNER
    if data == "owner:list_sub":
        subs = await subowners_col.find().to_list(None)
        if not subs:
            return await cb.answer("Belum ada sub-owner!", show_alert=True)

        teks = "👥 **LIST SUB-OWNER**\n\n"
        for s in subs:
            teks += f"• `{s['user_id']}` — until {s['expired']}\n"

        await cb.message.edit_text(teks, reply_markup=owner_panel_kb())

    # ADD SUB OWNER (trigger bot untuk meminta input username/ID)
    if data == "owner:add_sub":
        await cb.message.edit_text(
            "Kirim @username atau ID telegram user yang akan dijadikan **Sub-Owner 30 hari**"
        )
        # bot akan menunggu input → nanti kita buat di message handler next

    # MENU KELOLA PRODUK
    if data == "owner:menu_produk":
        await cb.message.edit_text("🛍 **KELOLA PRODUK**", reply_markup=produk_owner_kb())

    # LIST PRODUK
    if data == "owner:list_product":
        prods = await products_col.find().to_list(None)
        if not prods:
            return await cb.answer("Produk masih kosong!", show_alert=True)

        txt = "📃 **DAFTAR PRODUK**\n\n"
        for p in prods:
            txt += f"• {p['name']} — Rp{p['price']}\n"

        await cb.message.edit_text(txt, reply_markup=produk_owner_kb())

    # BACK KE PANEL OWNER
    if data == "owner:back_panel":
        await cb.message.edit_text("👑 **OWNER PANEL**", reply_markup=owner_panel_kb())

    await cb.answer()

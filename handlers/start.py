# handlers/start.py
import os
import logging
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

import config

logger = logging.getLogger("handlers.start")

# Allow override via .env: LOGO_URL (link gambar), CREATOR_NAME in config.py or env
LOGO_URL = getattr(config, "LOGO_URL", os.getenv("LOGO_URL", "") or None)
CREATOR_NAME = getattr(config, "CREATOR_NAME", os.getenv("CREATOR_NAME", "Unknown"))
OWNER_ID = getattr(config, "OWNER_ID", 0)


def _is_owner(user_id: int) -> bool:
    try:
        return int(user_id) == int(OWNER_ID)
    except Exception:
        return False


def register_start(app: Client):
    """
    Register /start handler and the initial menu callbacks.
    Call this from your main: register_start(app)
    """

    logger.info("Registering start handler")

    @app.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
        try:
            user = message.from_user
            user_mention = user.mention if user else "Pengguna"
            user_id = user.id if user else 0
            owner_flag = _is_owner(user_id)

            # Build header text: personalized + brand
            text_lines = [
                f"👋 Halo {user_mention}",
                f"🤖 𝐆𝐀𝐑𝐅𝐈𝐄𝐋𝐃 𝐒𝐓𝐎𝐑𝐄",
                f"👑 Creator: {CREATOR_NAME}",
                ""
            ]
            if owner_flag:
                text_lines.append("⚠️ Kamu login sebagai OWNER")
                text_lines.append("")

            text_lines.append("📌 Silakan pilih menu di bawah :")
            text = "\n".join(text_lines)

            # Buttons: Produk | Payment | Help | Support (+ owner admin)
            kb = [
                [
                    InlineKeyboardButton("🛍 Produk", callback_data="menu_product"),
                    InlineKeyboardButton("💳 Payment", callback_data="menu_payment"),
                ],
                [
                    InlineKeyboardButton("📘 Bantuan", callback_data="menu_help"),
                    InlineKeyboardButton("👥 Support", url=os.getenv("SUPPORT_URL", "https://t.me/storegarf")),
                ]
            ]

            # Owner extra buttons (admin panel + manage products)
            if owner_flag:
                kb.append([
                    InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu_owner"),
                    InlineKeyboardButton("➕ Manage Produk", callback_data="menu_manage_products")
                ])
            else:
                # For regular users we still include a Manage Produk button only if they are a sub-owner in the future.
                # Keep it hidden now.
                pass

            # If LOGO_URL set, send photo with caption; else send plain text message
            if LOGO_URL:
                try:
                    # send photo with inline keyboard and caption (caption uses text)
                    await message.reply_photo(
                        photo=LOGO_URL,
                        caption=text,
                        reply_markup=InlineKeyboardMarkup(kb)
                    )
                    return
                except Exception as e:
                    # fallback to normal reply if photo send failed
                    logger.warning("Failed to send logo photo in /start: %s", e)

            # Fallback: simple message reply
            await message.reply(text, reply_markup=InlineKeyboardMarkup(kb))

        except Exception as exc:
            logger.exception("Error in /start handler: %s", exc)
            # avoid crash; inform user gracefully
            try:
                await message.reply("⚠️ Terjadi kesalahan saat menampilkan menu. Coba lagi nanti.")
            except Exception:
                pass

    # -------------------------
    # CALLBACKS: menu actions
    # -------------------------
    @app.on_callback_query(filters.regex("^menu_product$"))
    async def cb_menu_product(client: Client, callback: CallbackQuery):
        try:
            # delegate to product handler via callback (product handler must listen to this)
            # If product handler not ready, show friendly message
            await callback.answer()  # acknowledge
            await callback.message.edit_text("🔁 Memuat daftar produk...")  # quick feedback
            # product handler should catch "menu_product" callback and replace message
        except Exception as e:
            logger.exception("cb_menu_product error: %s", e)
            await callback.answer("⚠️ Gagal memuat produk.", show_alert=True)

    @app.on_callback_query(filters.regex("^menu_payment$"))
    async def cb_menu_payment(client: Client, callback: CallbackQuery):
        try:
            await callback.answer()
            # Minimal instructions - payment flow handled by payment handler
            text = (
                "💳 Menu Pembayaran\n\n"
                "Silakan pilih metode pembayaran pada menu produk saat membeli.\n"
                "Jika butuh bantuan, klik Bantuan atau hubungi support."
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍 Lihat Produk", callback_data="menu_product")],
                [InlineKeyboardButton("📘 Bantuan", callback_data="menu_help")]
            ])
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception as e:
            logger.exception("cb_menu_payment error: %s", e)
            await callback.answer("⚠️ Gagal membuka menu pembayaran.", show_alert=True)

    @app.on_callback_query(filters.regex("^menu_help$"))
    async def cb_menu_help(client: Client, callback: CallbackQuery):
        try:
            await callback.answer()
            # Help content (both explanation + contact link)
            text = (
                "📘 *Bantuan & Panduan*\n\n"
                "• /produk — Lihat daftar produk yang tersedia\n"
                "• Pilih produk → ikuti instruksi pembayaran\n"
                "• Upload bukti → gunakan: /confirm <ORDER_ID> (reply ke foto bukti)\n\n"
                "Jika butuh bantuan langsung, hubungi admin:"
            )
            support_url = os.getenv("SUPPORT_URL", "https://t.me/storegarf")
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Hubungi Admin", url=support_url)],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]
            ])
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception as e:
            logger.exception("cb_menu_help error: %s", e)
            await callback.answer("⚠️ Gagal menampilkan bantuan.", show_alert=True)

    @app.on_callback_query(filters.regex("^menu_owner$"))
    async def cb_menu_owner(client: Client, callback: CallbackQuery):
        try:
            uid = callback.from_user.id
            if not _is_owner(uid):
                return await callback.answer("⛔️ Hanya owner yang bisa mengakses menu ini.", show_alert=True)

            await callback.answer()
            text = (
                "👑 *Owner Panel*\n\n"
                "Gunakan tombol di bawah untuk administrasi."
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Daftar Partner", callback_data="owner:partners")],
                [InlineKeyboardButton("🗄 Backup DB", callback_data="owner:backup")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]
            ])
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception as e:
            logger.exception("cb_menu_owner error: %s", e)
            await callback.answer("⚠️ Gagal membuka panel owner.", show_alert=True)

    @app.on_callback_query(filters.regex("^menu_manage_products$"))
    async def cb_manage_products(client: Client, callback: CallbackQuery):
        """
        Owner -> Manage Produk (CRUD). This callback only shows the management menu.
        Actual add/edit/delete should be implemented in handlers/product.py (listen to these callbacks).
        """
        try:
            uid = callback.from_user.id
            if not _is_owner(uid):
                return await callback.answer("⛔️ Hanya owner yang bisa mengatur produk.", show_alert=True)

            await callback.answer()
            text = (
                "➕ *Manage Produk*\n\n"
                "Pilih aksi:\n"
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Tambah Produk", callback_data="product:add")],
                [InlineKeyboardButton("✏️ Edit Produk", callback_data="product:edit")],
                [InlineKeyboardButton("🗑 Hapus Produk", callback_data="product:delete")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_owner")]
            ])
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception as e:
            logger.exception("cb_manage_products error: %s", e)
            await callback.answer("⚠️ Gagal membuka manage produk.", show_alert=True)

    @app.on_callback_query(filters.regex("^back_to_start$"))
    async def cb_back_to_start(client: Client, callback: CallbackQuery):
        try:
            await callback.answer()
            # Reuse /start by simulating calling the start handler: easiest is to call start_cmd's reply
            # But here we'll show a minimal main menu again
            user = callback.from_user
            user_mention = user.mention if user else "Pengguna"
            user_id = user.id if user else 0
            owner_flag = _is_owner(user_id)

            text_lines = [
                f"👋 Halo {user_mention}",
                f"🤖 𝐆𝐀𝐑𝐅𝐈𝐄𝐋𝐃 𝐒𝐓𝐎𝐑𝐄",
                f"👑 Creator: {CREATOR_NAME}",
                ""
            ]
            if owner_flag:
                text_lines.append("⚠️ Kamu login sebagai OWNER")
                text_lines.append("")
            text_lines.append("📌 Silakan pilih menu di bawah :")
            text = "\n".join(text_lines)

            kb = [
                [
                    InlineKeyboardButton("🛍 Produk", callback_data="menu_product"),
                    InlineKeyboardButton("💳 Payment", callback_data="menu_payment"),
                ],
                [
                    InlineKeyboardButton("📘 Bantuan", callback_data="menu_help"),
                    InlineKeyboardButton("👥 Support", url=os.getenv("SUPPORT_URL", "https://t.me/storegarf")),
                ]
            ]
            if owner_flag:
                kb.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu_owner")])
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            logger.exception("cb_back_to_start error: %s", e)
            await callback.answer("⚠️ Gagal kembali ke menu utama.", show_alert=True)

    # done
    logger.info("✅ start handler registered")

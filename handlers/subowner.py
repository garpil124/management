# handlers/subowner.py
from pyrogram import Client, filters
from pyrogram.types import Message
from db.mongo import partners_col, products_col
import datetime

@Client.on_message(filters.command("setstore") & filters.private)
async def set_store(client: Client, message: Message):
    """
    /setstore Nama Toko | https://link.banner.jpg
    """
    uid = message.from_user.id
    rec = await partners_col.find_one({"owner_id": uid})
    if not rec:
        return await message.reply("❌ Kamu bukan partner terdaftar. Minta owner tambah dengan /addpartner")

    payload = message.text.partition(" ")[2]
    if not payload:
        return await message.reply("Usage: /setstore Nama Toko | https://link.banner.jpg")

    name, _, banner = payload.partition("|")
    update = {"store": name.strip()}
    if banner and banner.strip():
        update["banner"] = banner.strip()
    await partners_col.update_one({"_id": rec["_id"]}, {"$set": update})
    await message.reply("✅ Store info updated.")

@Client.on_message(filters.command("addproduct") & filters.private)
async def add_product(client: Client, message: Message):
    """
    /addproduct name | price | desc
    """
    uid = message.from_user.id
    rec = await partners_col.find_one({"owner_id": uid})
    if not rec:
        return await message.reply("❌ Kamu bukan partner")

    payload = message.text.partition(" ")[2]
    if not payload:
        return await message.reply("Usage: /addproduct name | price | desc")

    try:
        name, _, rest = payload.partition("|")
        price_s, _, desc = rest.partition("|")
        price = int(price_s.strip())
        doc = {
            "owner_id": uid,
            "name": name.strip(),
            "price": price,
            "desc": desc.strip(),
            "created_at": datetime.datetime.utcnow()
        }
        res = await products_col.insert_one(doc)
        await message.reply(f"✅ Product added: {res.inserted_id}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

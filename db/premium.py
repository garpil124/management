from db.mongo import db
from datetime import datetime, timedelta

premium_col = db["premium"]

async def add_premium(user_id: int, days: int = 30):
    expired = datetime.utcnow() + timedelta(days=days)
    await premium_col.update_one(
        {"user_id": user_id},
        {"$set": {"expired": expired}},
        upsert=True
    )
    return expired

async def remove_premium(user_id: int):
    await premium_col.delete_one({"user_id": user_id})

async def get_premium(user_id: int):
    return await premium_col.find_one({"user_id": user_id})

async def is_premium(user_id: int):
    data = await get_premium(user_id)
    if not data:
        return False
    if data["expired"] < datetime.utcnow():
        await remove_premium(user_id)
        return False
    return True

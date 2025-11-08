import asyncio
from typing import Optional
from pyrogram import Client
import config

async def safe_send(client: Client, chat_id: int, text: str, **kwargs):
    try:
        return await client.send_message(chat_id, text, **kwargs)
    except Exception as e:
        # gentle retry
        try:
            await asyncio.sleep(1)
            return await client.send_message(chat_id, text, **kwargs)
        except Exception:
            print("safe_send failed:", e)
            return None

async def send_log_all(client: Client, text: str, parse_mode: Optional[str] = "html"):
    if config.LOG_CHANNEL_ID:
        try:
            await safe_send(client, config.LOG_CHANNEL_ID, text, parse_mode=parse_mode)
        except Exception as e:
            print("send_log_all channel error:", e)
    if config.LOG_GROUP_ID:
        try:
            await safe_send(client, config.LOG_GROUP_ID, text, parse_mode=parse_mode)
        except Exception as e:
            print("send_log_all group error:", e)

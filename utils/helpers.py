from pyrogram import Client
from typing import Optional

async def safe_send(
    client: Client,
    chat_id: int,
    text: str,
    reply_markup=None,
    disable_web_page_preview: Optional[bool] = True
):
    try:
        return await client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview
        )
    except Exception as e:
        print(f"[SAFE_SEND ERROR] {e}")
        return None


def human_readable(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

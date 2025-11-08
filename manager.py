import os
import asyncio
import logging
from pyrogram import Client
from db.mongo import partners_col
from config import API_ID, API_HASH
import importlib

log = logging.getLogger("Manager")
clients = {}

async def start_partner(doc):
    token = doc.get("bot_token")
    pid = str(doc.get("_id"))
    name = f"partner_{pid}"
    if name in clients:
        return
    app = Client(name, api_id=API_ID, api_hash=API_HASH, bot_token=token, plugins={'root':'handlers'})
    await app.start()
    clients[name] = app
    log.info("Started partner %s", pid)

async def spawn_all():
    rows = await partners_col.find({"bot_token":{"$exists":True}}).to_list(length=1000)
    for r in rows:
        try:
            await start_partner(r)
        except Exception as e:
            log.exception("start_partner error: %s", e)

async def watch_loop():
    while True:
        try:
            await spawn_all()
        except Exception as e:
            log.exception("watch error: %s", e)
        await asyncio.sleep(10)

def start_manager(loop):
    asyncio.run_coroutine_threadsafe(watch_loop(), loop)

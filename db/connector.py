# db/connector.py
import logging
from db import mongo

logger = logging.getLogger("DBConnector")

async def connect_db(uri: str = None, db_name: str = None):
    """
    If db.mongo already created client/db, this is a no-op.
    Keberadaan function ini kompatibel dengan main.py.
    """
    # db.mongo uses AsyncIOMotorClient and already connects on import.
    logger.info("DB connect noop - using db.mongo client")

def get_db():
    """
    Return motor async database object from db.mongo
    """
    try:
        return mongo.db
    except Exception as e:
        logger.exception("Failed to get db from db.mongo: %s", e)
        return None

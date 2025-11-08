# Simple helpers for collection access
from db.connector import get_db


def bots_col():
    db = get_db()
    return db.bots if db else None


def subowners_col():
    db = get_db()
    return db.subowners if db else None


def products_col():
    db = get_db()
    return db.products if db else None


def orders_col():
    db = get_db()
    return db.orders if db else None

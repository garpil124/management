from datetime import datetime, timedelta
import pytz

WIB = pytz.timezone("Asia/Jakarta")

def now_wib():
    return datetime.now(WIB)

def now_wib_str():
    return now_wib().strftime("%Y-%m-%d %H:%M:%S")

def days_from_now(days: int):
    return now_wib() + timedelta(days=days)

def format_wib(dt: datetime):
    return dt.astimezone(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")

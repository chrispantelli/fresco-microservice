from datetime import datetime
import time    

def format_date(iso_str: str) -> str:
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.strftime("%d %B %Y")

def current_date_epoch() -> str:
    return int(time.time())
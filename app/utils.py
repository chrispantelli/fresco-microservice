from datetime import datetime
from collections import defaultdict
from typing import Any
import time    

def format_date(iso_str: str) -> str:
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.strftime("%d %B %Y")

def current_date_epoch() -> str:
    return int(time.time())

def to_float(value: Any) -> float:
    if value in (None, "", "null"):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
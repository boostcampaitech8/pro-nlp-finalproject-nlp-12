import base64
from typing import Optional


def encode_cursor(offset: int) -> str:
    raw = str(int(offset)).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        return int(raw)
    except Exception:
        return 0

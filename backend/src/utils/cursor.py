"""커서 기반 페이지네이션 유틸리티"""
import base64
from typing import Optional


def encode_cursor(offset: int) -> str:
    """offset을 base64 커서로 인코딩"""
    raw = str(int(offset)).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: Optional[str]) -> int:
    """base64 커서를 offset으로 디코딩"""
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        return int(raw)
    except Exception:
        return 0

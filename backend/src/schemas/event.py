"""이벤트 관련 스키마"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional


# ===== Request =====
class EventCreate(BaseModel):
    """사용자 이벤트 기록 요청"""
    user_id: str = Field(..., min_length=1, description="로그인 유저ID 또는 세션ID")
    paper_id: int
    event_type: Literal["impression", "click", "like", "bookmark", "dislike"]
    weight: float = Field(default=1.0, ge=0.0, le=10.0)


# ===== Response =====
class EventResponse(BaseModel):
    """사용자 이벤트 기록 응답"""
    ok: bool
    event_id: Optional[int] = None      # 토글 해제 시 None
    user_id: str
    paper_id: int
    event_type: str
    toggled_off: bool = False           # True면 토글 해제됨 (like/bookmark 취소)
    click_count: Optional[int] = None   # click 이벤트일 때만 반환


# ===== ORM 직렬화용 =====
class EventOut(BaseModel):
    """DB 이벤트 조회 응답"""
    id: int
    user_id: str
    paper_id: int
    event_type: str
    created_at: datetime

    class Config:
        from_attributes = True

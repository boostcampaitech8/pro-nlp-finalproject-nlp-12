"""이벤트 관련 스키마"""
from pydantic import BaseModel, Field
from typing import Literal


class UserEventRequest(BaseModel):
    """사용자 이벤트 기록 요청"""
    user_id: str = Field(..., min_length=1)
    paper_id: int
    event_type: Literal["click", "like", "bookmark", "dislike"]
    weight: float = Field(default=1.0, ge=0.0, le=10.0)


class UserEventResponse(BaseModel):
    """사용자 이벤트 기록 응답"""
    ok: bool
    event_id: int
    user_id: str
    paper_id: int
    event_type: str

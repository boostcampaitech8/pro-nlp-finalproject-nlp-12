"""이벤트 관련 스키마"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class UserEventRequest(BaseModel):
    """사용자 이벤트 기록 요청"""
    user_id: str = Field(..., min_length=1)
    paper_id: int
    event_type: Literal["click", "like", "bookmark", "dislike"]
    weight: float = Field(default=1.0, ge=0.0, le=10.0)


### 수정사항: 토글/클릭 응답 필드 추가
class UserEventResponse(BaseModel):
    """사용자 이벤트 기록 응답"""
    ok: bool
    event_id: Optional[int] = None  # 토글 해제 시 None
    user_id: str
    paper_id: int
    event_type: str
    toggled_off: bool = False  # True면 토글 해제됨 (like/bookmark 취소)
    click_count: Optional[int] = None  # click 이벤트일 때만 반환

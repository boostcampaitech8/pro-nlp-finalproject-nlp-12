from datetime import datetime
from pydantic import BaseModel, Field

class EventCreate(BaseModel):
    user_id: str = Field(..., description="로그인 유저ID 또는 세션ID")
    paper_id: int
    event_type: str = Field(..., description="impression/click/like/bookmark/dislike")

class EventOut(BaseModel):
    id: int
    user_id: str
    paper_id: int
    event_type: str
    created_at: datetime

    class Config:
        from_attributes = True  # pydantic v2 (v1이면 orm_mode = True)

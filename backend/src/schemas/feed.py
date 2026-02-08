from pydantic import BaseModel, HttpUrl
from datetime import date
from typing import Optional, List

# [수정] authors & abstract 삭제, summary 추가
class FeedItem(BaseModel):
    paper_id: int
    arxiv_id: str
    title: str

    summary: Optional[str] = None

    primary_category: Optional[str] = None
    categories: Optional[str] = None
    published_date: Optional[date] = None

    abs_url: HttpUrl
    pdf_url: HttpUrl

    is_bookmarked: Optional[bool] = False
    is_liked: Optional[bool] = False


class FeedResponse(BaseModel):
    user_id: str

    k: Optional[int] = None

    limit: Optional[int] = None

    items: List[FeedItem]

    # 무한 스크롤용
    next_cursor: Optional[str] = None
    has_more: bool = False

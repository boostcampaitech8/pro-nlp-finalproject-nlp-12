from pydantic import BaseModel, HttpUrl
from datetime import date
from typing import Optional, List

class FeedItem(BaseModel):
    paper_id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: str

    primary_category: Optional[str] = None
    categories: Optional[str] = None
    published_at: Optional[str] = None

    abs_url: Optional[str] = None
    pdf_url: Optional[str] = None

    score: float

    """
    논문 추천 결과를 관리하는 스키마입니다.
    """
    paper_id: int
    arxiv_id: str
    title: str
    pdf_url: HttpUrl
    abs_url: HttpUrl
    published_date: date
    summary: str
    is_liked: bool
    is_bookmarked: bool

class FeedResponse(BaseModel):
    user_id: str

    k: Optional[int] = None

    limit: Optional[int] = None

    items: List[FeedItem]

    # 무한 스크롤용
    next_cursor: Optional[str] = None
    has_more: bool = False

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

class FeedResponse(BaseModel):
    user_id: str

    k: Optional[int] = None

    limit: Optional[int] = None

    items: List[FeedItem]

    # 무한 스크롤용
    next_cursor: Optional[str] = None
    has_more: bool = False

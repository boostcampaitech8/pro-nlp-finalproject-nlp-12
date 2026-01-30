"""피드 및 추천 관련 스키마"""
from pydantic import BaseModel
from typing import Optional


class FeedItem(BaseModel):
    """추천 피드 아이템"""
    paper_id: int
    arxiv_id: str
    title: str
    abstract: Optional[str] = None
    authors: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: int = 0
    published_date: Optional[str] = None


class FeedResponse(BaseModel):
    """피드 응답"""
    items: list[FeedItem]
    total: int
    sources_used: list[str]  # ["faiss", "category", "popular"]
    has_more: bool
    timings: Optional[dict] = None  # 성능 측정용

"""피드 및 추천 관련 스키마"""
from pydantic import BaseModel
from typing import Optional, List


class FeedItem(BaseModel):
    """추천 피드 아이템"""
    paper_id: int
    arxiv_id: str
    title: str
    abstract: Optional[str] = None

    # 카테고리 정보
    primary_category: Optional[str] = None
    categories: Optional[str] = None

    # 날짜 정보
    published_date: Optional[str] = None

    # URL 정보
    abs_url: Optional[str] = None
    pdf_url: Optional[str] = None

    # 점수/통계 정보
    score: Optional[float] = None       # 추천 점수
    citation_count: int = 0             # 인용 수 (paper_v5)



class FeedResponse(BaseModel):
    """피드 응답"""
    user_id: Optional[str] = None

    # 페이징 정보
    k: Optional[int] = None             # 요청한 개수 (feature_baseline)
    limit: Optional[int] = None         # (feature_baseline)
    total: Optional[int] = None         # 전체 개수 (paper_v5)
    
    # 데이터
    items: List[FeedItem]

    # 커서 페이지네이션 (feature_baseline)
    next_cursor: Optional[str] = None
    has_more: bool = False

    # 디버깅/분석 정보
    sources_used: Optional[List[str]] = None        # ["faiss", "category"]
    timings: Optional[dict] = None                  # 성능 측정용 

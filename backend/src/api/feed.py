"""피드 추천 API"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.schemas.feed import FeedResponse, FeedItem
from src.service.recommend_service import RecommendService

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("", response_model=FeedResponse)
def get_feed(
    user_id: str = Query(..., min_length=1),
    k: int = Query(default=30, ge=1, le=100),
    use_faiss: bool = Query(default=True),
    use_arxiv: bool = Query(default=True),
    use_category: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """
    개인화 추천 피드
    
    Query Parameters:
    - user_id: 사용자 ID
    - k: 반환할 논문 수 (1-100)
    - use_faiss: FAISS 벡터 검색 사용
    - use_arxiv: arXiv 실시간 검색 사용
    - use_category: 카테고리 기반 검색 사용
    """
    try:
        service = RecommendService(db)
        result = service.recommend(
            user_id=user_id,
            k=k,
            use_faiss=use_faiss,
            use_arxiv=use_arxiv,
            use_category=use_category,
        )
        
        items = [FeedItem(**item) for item in result["items"]]
        
        return FeedResponse(
            items=items,
            total=len(items),
            sources_used=result["sources_used"],
            has_more=len(items) >= k,
            timings=result.get("timings"),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

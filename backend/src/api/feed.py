"""피드 추천 API - 빠른 추천 + 느린 추천"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.schemas.feed import FeedResponse, FeedItem
from src.service.feed_service import FeedService
from src.service.recommend_service import RecommendService

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("", response_model=FeedResponse)
def get_feed(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    k: int | None = Query(default=None),  # legacy support
    db: Session = Depends(get_db),
):
    """
    빠른 개인화 추천 피드 (저장된 벡터 기반)

    - 커서 페이지네이션 지원
    - 사용자 벡터가 dirty 상태면 자동 갱신
    - Cold start 시 최신 논문 fallback
    """
    if k is not None:
        limit = k

    try:
        service = FeedService(db)
        items, next_cursor, has_more = service.recommend_feed(
            user_id=user_id,
            limit=limit,
            cursor=cursor,
        )

        return FeedResponse(
            user_id=user_id,
            k=k,
            limit=limit,
            items=[FeedItem(**item) for item in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slow", response_model=FeedResponse)
def get_feed_slow(
    user_id: str = Query(..., min_length=1),
    k: int = Query(default=30, ge=1, le=100),
    use_faiss: bool = Query(default=True),
    use_category: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """
    느린 개인화 추천 피드 (LLM 실시간 쿼리 기반)

    - 온보딩 데이터 기반 실시간 preference query 생성
    - FAISS + 카테고리 검색 병합
    - 복합 스코어링 (벡터 유사도 + 키워드 + 최신성 + 소스)
    """
    try:
        service = RecommendService(db)
        result = service.recommend(
            user_id=user_id,
            k=k,
            use_faiss=use_faiss,
            use_category=use_category,
        )

        items = [FeedItem(**item) for item in result["items"]]

        return FeedResponse(
            user_id=user_id,
            items=items,
            total=len(items),
            sources_used=result["sources_used"],
            has_more=len(items) >= k,
            timings=result.get("timings"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

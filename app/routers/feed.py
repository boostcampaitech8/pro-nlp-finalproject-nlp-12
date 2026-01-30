from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.feed import FeedResponse, FeedItem
from app.services.recsys_service import RecSysService

router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("", response_model=FeedResponse)
def get_feed(
    user_id: str,
    limit: int = 20,
    cursor: str | None = None,
    # 일단 살려: /feed?user_id=u1&k=5 도 계속 되게 test user
    k: int | None = None,
    db: Session = Depends(get_db),
):
    if k is not None:
        limit = k

    svc = RecSysService(db)

    items, next_cursor, has_more = svc.recommend_page(
        user_id=user_id,
        limit=limit,
        cursor=cursor,
        candidate_k=max(200, limit * 50),
        seen_limit=3000,
    )

    return FeedResponse(
        user_id=user_id,
        k=k,
        limit=limit,
        items=[FeedItem(**x) for x in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )

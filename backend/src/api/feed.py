from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.mysql import get_mysql_db
from src.schemas.feed import FeedResponse, FeedItem
from src.service.recsys_service import RecSysService
from src.service.smart_recommend_service import SmartRecommendService
from src.database.valkey import get_valkey_db
from src.service.paper_service import PaperService
from src.api.dependencies import get_paper_service
from redis import asyncio

router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("", response_model=FeedResponse)
async def get_feed(
    user_id: str,
    limit: int = 20,
    cursor: str | None = None,
    # /feed?user_id=u1&k=5 테스트용
    k: int | None = None,
    mode: str = Query("quick", pattern="^(quick|smart|fast)$"),
    db: Session = Depends(get_mysql_db),
    paper_service: PaperService = Depends(get_paper_service),
    valkey: asyncio.Redis = Depends(get_valkey_db)
):
    if k is not None:
        limit = k

    if mode == "smart":
        smart = SmartRecommendService(db, paper_service, valkey)
        out = await smart.recommend(user_id=user_id, k=limit)
        items = out.get("items", [])
        next_cursor = None
        has_more = False
    else:
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

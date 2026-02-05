"""라이브러리 API - 사용자 좋아요/북마크 목록"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.schemas.library import LibraryResponse, LibraryItem
from src.repository.library_repository import LibraryRepository
from src.repository.user_repository import UserRepository

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/library", response_model=LibraryResponse)
def get_my_library(
    user_id: str = Query(..., description="사용자 UUID"),
    type: str = Query("all", pattern="^(all|like|bookmark)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    내 라이브러리 조회 (좋아요/북마크한 논문)

    Query Parameters:
    - user_id: 사용자 UUID
    - type: all(전체), like(좋아요만), bookmark(북마크만)
    - limit: 반환할 논문 수
    - offset: 시작 위치
    """
    # UUID → 내부 ID 변환
    user_repo = UserRepository(db)
    user = user_repo.get_by_uuid(user_id)
    if not user:
        return LibraryResponse(
            user_id=user_id,
            type=type,
            limit=limit,
            offset=offset,
            total=0,
            items=[],
        )

    repo = LibraryRepository(db)
    total, items = repo.list_library(
        user_id=user.id,
        event_type=type,
        limit=limit,
        offset=offset,
    )

    return LibraryResponse(
        user_id=user_id,
        type=type,
        limit=limit,
        offset=offset,
        total=total,
        items=[LibraryItem(**x) for x in items],
    )

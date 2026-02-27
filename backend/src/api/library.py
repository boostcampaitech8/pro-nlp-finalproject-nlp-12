from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.mysql import get_mysql_db
from src.schemas.library import LibraryResponse, LibraryItem
from src.repository.library_repo import LibraryRepository

router = APIRouter(
    prefix="/me",
    tags=["me"]
)


@router.get("/library", response_model=LibraryResponse)
def get_my_library(
    user_id: str = Query(..., description="e.g. u1"),
    type: str = Query("all", pattern="^(all|like|bookmark)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_mysql_db),
):
    repo = LibraryRepository(db)
    total, items = repo.list_library(user_id=user_id, event_type=type, limit=limit, offset=offset)

    return LibraryResponse(
        user_id=user_id,
        type=type,
        limit=limit,
        offset=offset,
        total=total,
        items=[LibraryItem(**x) for x in items],
    )

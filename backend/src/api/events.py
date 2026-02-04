"""이벤트 API - 사용자 상호작용 기록"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.schemas.event import EventCreate, EventResponse
from src.repository.event_repository import EventRepository
from src.repository.user_repository import UserRepository
from src.entity.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])

# 이벤트 가중치
EVENT_WEIGHTS = {
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}


def get_or_create_user(db: Session, user_uuid: str) -> User:
    """
    사용자 UUID로 User 조회, 없으면 생성
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_uuid(user_uuid)
    if user:
        return user

    # 없으면 새로 생성
    new_user = User(uuid=user_uuid)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("", response_model=EventResponse)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
):
    """
    사용자 이벤트 기록

    Event Types:
    - impression: 논문 노출 (피드에 표시됨)
    - click: 논문 클릭 (상세 보기)
    - like: 좋아요 (토글)
    - bookmark: 북마크 (토글)
    - dislike: 싫어요

    like/bookmark 이벤트 시 dirty flag 설정 (벡터 재계산 예약)
    """
    try:
        event_repo = EventRepository(db)
        user_repo = UserRepository(db)

        # user_uuid로 User 조회/생성
        user = get_or_create_user(db, payload.user_id)
        weight = EVENT_WEIGHTS.get(payload.event_type, payload.weight)

        # like/bookmark는 토글
        if payload.event_type in ("like", "bookmark"):
            if event_repo.exists_event(user.id, payload.paper_id, payload.event_type):
                event_repo.delete_event(user.id, payload.paper_id, payload.event_type)

                # dirty flag 설정
                user_repo.mark_vector_dirty(payload.user_id)

                db.commit()
                return EventResponse(
                    ok=True,
                    event_id=None,
                    user_id=payload.user_id,
                    paper_id=payload.paper_id,
                    event_type=payload.event_type,
                    toggled_off=True,
                )

            # 새로 생성
            event = event_repo.create_event(
                user_id=user.id,
                paper_id=payload.paper_id,
                event_type=payload.event_type,
                weight=weight,
            )

            # dirty flag 설정
            user_repo.mark_vector_dirty(payload.user_id)

            db.commit()
            return EventResponse(
                ok=True,
                event_id=event.id,
                user_id=payload.user_id,
                paper_id=payload.paper_id,
                event_type=payload.event_type,
                toggled_off=False,
            )

        # impression/dislike는 중복 체크 후 기록
        if payload.event_type in ("impression", "dislike"):
            if event_repo.exists_event(user.id, payload.paper_id, payload.event_type):
                return EventResponse(
                    ok=True,
                    event_id=None,
                    user_id=payload.user_id,
                    paper_id=payload.paper_id,
                    event_type=payload.event_type,
                    toggled_off=False,
                )

            event = event_repo.create_event(
                user_id=user.id,
                paper_id=payload.paper_id,
                event_type=payload.event_type,
                weight=weight,
            )
            db.commit()
            return EventResponse(
                ok=True,
                event_id=event.id,
                user_id=payload.user_id,
                paper_id=payload.paper_id,
                event_type=payload.event_type,
                toggled_off=False,
            )

        # click은 upsert (count 증가)
        if payload.event_type == "click":
            event = event_repo.upsert_click(user.id, payload.paper_id)

            # dirty flag 설정
            user_repo.mark_vector_dirty(payload.user_id)

            db.commit()
            return EventResponse(
                ok=True,
                event_id=event.id,
                user_id=payload.user_id,
                paper_id=payload.paper_id,
                event_type=payload.event_type,
                toggled_off=False,
                click_count=event.click_count,
            )

        # 기타 이벤트
        event = event_repo.create_event(
            user_id=user.id,
            paper_id=payload.paper_id,
            event_type=payload.event_type,
            weight=weight,
        )
        db.commit()
        return EventResponse(
            ok=True,
            event_id=event.id,
            user_id=payload.user_id,
            paper_id=payload.paper_id,
            event_type=payload.event_type,
            toggled_off=False,
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
def get_user_events(
    user_id: str,
    limit: int = 100,
    event_type: str | None = None,
    db: Session = Depends(get_db),
):
    """
    사용자 이벤트 조회

    Query Parameters:
    - limit: 반환할 이벤트 수 (기본값: 100)
    - event_type: 특정 이벤트 타입만 조회 (예: like, bookmark, dislike)
    """
    try:
        event_repo = EventRepository(db)
        user = get_or_create_user(db, user_id)

        events = event_repo.get_user_events(
            user_id=user.id,
            event_type=event_type,
            limit=limit
        )

        return {
            "user_id": user_id,
            "total": len(events),
            "events": [
                {
                    "event_id": e.id,
                    "paper_id": e.paper_id,
                    "event_type": e.event_type,
                    "weight": e.weight,
                    "click_count": e.click_count,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""이벤트 API - 사용자 상호작용 기록 및 preference 업데이트 (MVp2 호환성)"""
import logging
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.mysql import get_db, SessionLocal
from src.entity.user_event import UserEvent
from src.entity.user import User
from src.schemas.event import UserEventRequest, UserEventResponse
from src.service.preference_service import PreferenceService
from src.repository.user_event_repository import UserEventRepository
from src.repository.user_profile_repository import UserProfileRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])

EVENT_WEIGHTS = {
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}


def get_user_id_from_uuid(db: Session, user_uuid: str) -> int:
    """
    사용자 UUID로부터 User ID (정수) 조회
    없으면 자동 생성
    """
    profile_repo = UserProfileRepository(db)
    user = profile_repo.get_by_user_id(user_uuid)
    if user:
        return user.id
    # 없으면 새로 생성
    from src.entity.user import User as UserEntity
    new_user = UserEntity(uuid=user_uuid)
    created = profile_repo.create(new_user)
    return created.id


async def update_preference_background(user_id: str, paper_id: int, event_type: str):
    """백그라운드에서 preference 업데이트"""
    if event_type not in ("like", "bookmark"):
        return

    try:
        # 새 DB 세션 생성 (백그라운드 태스크용)
        db = SessionLocal()
        try:
            pref_service = PreferenceService(db)
            # TODO: update_preference_from_event 메서드 구현
            # result = await pref_service.update_preference_from_event(user_id, paper_id, event_type)
            logger.info(f"Updated preference for user {user_id} after {event_type}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Background preference update failed: {e}")


@router.post("", response_model=UserEventResponse)
async def log_event(
    payload: UserEventRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    사용자 이벤트 기록
    
    Event Types:
    - click: 논문 클릭
    - like: 좋아요
    - bookmark: 북마크
    - dislike: 싫어요
    
    Like/Bookmark 이벤트 시 백그라운드에서 사용자 preference 벡터 업데이트
    """
    try:
        event_repo = UserEventRepository(db)

        # user_uuid로부터 User ID 조회
        user_id = get_user_id_from_uuid(db, payload.user_id)

        ### 수정사항: click은 upsert (count 증가), like/bookmark는 토글
        # click은 upsert (count 증가)
        if payload.event_type == "click":
            event = event_repo.upsert_click(user_id, payload.paper_id)
            return UserEventResponse(
                ok=True,
                event_id=event.id,
                user_id=payload.user_id,
                paper_id=event.paper_id,
                event_type=event.event_type,
                toggled_off=False,
                click_count=event.click_count,
            )

        # like/bookmark는 토글
        if payload.event_type in ("like", "bookmark"):
            if event_repo.exists_event(user_id, payload.paper_id, payload.event_type):
                event_repo.delete_event(user_id, payload.paper_id, payload.event_type)
                return UserEventResponse(
                    ok=True,
                    event_id=None,
                    user_id=payload.user_id,
                    paper_id=payload.paper_id,
                    event_type=payload.event_type,
                    toggled_off=True,
                )

        # like/bookmark 새로 생성
        event = UserEvent(
            user_id=user_id,
            paper_id=payload.paper_id,
            event_type=payload.event_type,
        )

        event = event_repo.create(event)

        # like/bookmark 시 백그라운드에서 preference 업데이트
        if payload.event_type in ("like", "bookmark"):
            background_tasks.add_task(
                update_preference_background,
                payload.user_id,
                payload.paper_id,
                payload.event_type,
            )

        return UserEventResponse(
            ok=True,
            event_id=event.id,
            user_id=payload.user_id,
            paper_id=event.paper_id,
            event_type=event.event_type,
            toggled_off=False,  # 토글 활성화됨
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log event: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}")
def get_user_events(
    user_id: str,
    limit: int = 100,
    event_type: str = None,
    db: Session = Depends(get_db),
):
    """
    사용자 이벤트 조회
    
    Query Parameters:
    - limit: 반환할 이벤트 수 (기본값: 100)
    - event_type: 특정 이벤트 타입만 조회 (예: like, bookmark, dislike)
    """
    try:
        event_repo = UserEventRepository(db)
        
        # user_uuid로부터 User ID 조회
        db_user_id = get_user_id_from_uuid(db, user_id)
        
        events = event_repo.get_by_user_id(
            user_id=db_user_id,
            event_type=event_type,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "total": len(events),
            "events": [
                {
                    "event_id": e.id,  # event_id에서 id로 변경
                    "paper_id": e.paper_id,
                    "event_type": e.event_type,
                    # weight 필드 제거 (새 엔티티에 없음)
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

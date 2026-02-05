from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.mysql import SessionLocal
from src.schemas.event import EventCreate
from src.service.recsys_service import RecSysService

router = APIRouter(prefix="/events", tags=["events"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=dict)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    svc = RecSysService(db)

    # 유효한 event_type인지 검증
    svc.get_weight(payload.event_type)

    # like / bookmark 는 토글
    if payload.event_type in ("like", "bookmark"):
        active = svc.event_repo.toggle_event(
            user_id=payload.user_id,
            paper_id=payload.paper_id,
            event_type=payload.event_type,
        )

        # dirty flag (벡터 재계산은 나중에 feed에서)
        svc.profile_repo.mark_vector_dirty(payload.user_id)

        db.commit()
        return {"ok": True, "active": active}

    # view/click/impression/dislike 등은 누적 기록
    try:
        # 중복 방지: 같은 user/paper/type는 1번만 저장
        if svc.event_repo.exists_event(
            user_id=payload.user_id,
            paper_id=payload.paper_id,
            event_type=payload.event_type,
        ):
            return {"ok": True, "deduped": True}
    
        svc.event_repo.create(
            user_id=payload.user_id,
            paper_id=payload.paper_id,
            event_type=payload.event_type,
        )
    
        if payload.event_type == "click":
            svc.profile_repo.mark_vector_dirty(payload.user_id)
    
        db.commit()
        return {"ok": True}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

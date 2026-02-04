"""Admin API - 시스템 관리 엔드포인트"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from src.database.mysql import get_db
from src.entity.paper import Paper
from src.entity.user_event import UserEvent
from src.service.ingest_service import IngestService
from src.api.events import get_or_create_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/sync")
def sync_papers_to_faiss(
    batch_size: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """
    논문 DB를 FAISS에 동기화 (중복 제외, 증분 동기화)

    - 이미 인덱싱된 논문은 스킵
    - batch_size 단위로 처리
    """
    try:
        service = IngestService(db)
        ### 수정사항: batch_size → limit 파라미터명 맞춤
        result = service.sync_papers_to_faiss(limit=batch_size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex_faiss_all")
def reindex_faiss_all(
    batch_size: int = Query(default=1000, ge=1, le=10000),
    start_offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    FAISS 인덱스 전체 재구축

    - 기존 인덱스 초기화
    - 모든 논문 재인덱싱
    """
    try:
        service = IngestService(db)
        result = service.reindex_faiss_all(
            batch_size=batch_size,
            start_offset=start_offset,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-faiss")
def clear_faiss(db: Session = Depends(get_db)):
    """FAISS 인덱스 초기화 (모든 벡터 삭제) - 개발/디버깅용"""
    try:
        service = IngestService(db)
        ### 수정사항: FaissStore 메서드명에 맞게 수정 (clear→reset, count→total_count)
        service.faiss.reset()
        return {
            "message": "FAISS index cleared",
            "total_in_index": service.faiss.total_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """시스템 통계"""
    try:
        service = IngestService(db)
        stats = service.get_index_stats()

        # DB 논문 수
        paper_count = db.execute(select(func.count(Paper.id))).scalar() or 0

        return {
            "db_papers": paper_count,
            "faiss_total": stats["total_vectors"],
            "faiss_dimension": stats["dimension"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Event 관리 ============

@router.delete("/events/click")
def reset_click(
    user_id: str = Query(..., description="유저 UUID"),
    paper_id: int = Query(..., description="논문 ID"),
    db: Session = Depends(get_db),
):
    """특정 유저의 논문 클릭 기록 삭제"""
    user = get_or_create_user(db, user_id)

    stmt = select(UserEvent).where(
        and_(
            UserEvent.user_id == user.id,
            UserEvent.paper_id == paper_id,
            UserEvent.event_type == "click"
        )
    )
    event = db.execute(stmt).scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Click event not found")

    db.delete(event)
    db.commit()

    return {"message": "Click event deleted", "user_id": user_id, "paper_id": paper_id}


@router.delete("/events/user/{user_id}")
def delete_user_events(
    user_id: str,
    event_type: str | None = Query(None, description="특정 이벤트 타입만 삭제 (없으면 전체)"),
    db: Session = Depends(get_db),
):
    """특정 유저의 모든 이벤트 삭제"""
    user = get_or_create_user(db, user_id)

    stmt = select(UserEvent).where(UserEvent.user_id == user.id)
    if event_type:
        stmt = stmt.where(UserEvent.event_type == event_type)

    events = db.execute(stmt).scalars().all()
    count = len(events)

    for event in events:
        db.delete(event)
    db.commit()

    return {"message": f"Deleted {count} events", "user_id": user_id, "event_type": event_type}

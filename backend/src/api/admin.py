"""Admin API - 시스템 관리 엔드포인트"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from src.database.mysql import get_db
from src.entity.paper import Paper
from src.entity.user_event import UserEvent
from src.service.faiss_service import faiss_service
from src.service.embedder_service import embed_texts
from src.api.events import get_user_id_from_uuid

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/sync")
def sync_to_faiss(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    """
    논문 DB를 FAISS에 동기화 (중복 제외)

    - offset: 시작 위치
    - limit: 처리할 논문 수
    """
    # DB에서 논문 조회
    stmt = (
        select(Paper)
        .order_by(Paper.id)
        .offset(offset)
        .limit(limit)
    )
    papers = db.execute(stmt).scalars().all()

    if not papers:
        return {"synced": 0, "skipped": 0, "message": "No papers to sync"}

    # 이미 FAISS에 있는 paper_id 조회
    existing_ids = faiss_service.get_existing_paper_ids()
    print(f"Already in FAISS: {len(existing_ids)} papers")

    # 중복 제외하고 새 논문만 필터링
    docs = []
    paper_ids = []
    metadatas = []
    skipped = 0

    for p in papers:
        if p.id in existing_ids:
            skipped += 1
            continue

        text = f"{p.title}\n\n{p.abstract or ''}"
        docs.append(text)
        paper_ids.append(p.id)
        metadatas.append({
            "arxiv_id": p.arxiv_id,
        })

    if not docs:
        return {
            "synced": 0,
            "skipped": skipped,
            "message": "All papers already in FAISS",
            "total_in_index": faiss_service.get_total_count(),
        }

    # 임베딩 생성
    print(f"Embedding {len(docs)} new papers (skipped {skipped} existing)...")
    embeddings = embed_texts(docs)

    # FAISS에 추가
    faiss_service.add_papers(paper_ids, embeddings, metadatas)

    return {
        "synced": len(paper_ids),
        "skipped": skipped,
        "total_in_index": faiss_service.get_total_count(),
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """시스템 통계"""
    # DB 논문 수
    paper_count = db.execute(select(Paper)).scalars().all()

    return {
        "db_papers": len(paper_count),
        "faiss_total": faiss_service.get_total_count(),
    }


### 수정사항: FAISS 인덱스 초기화 엔드포인트 추가
@router.post("/clear-faiss")
def clear_faiss():
    """FAISS 인덱스 초기화 (모든 벡터 삭제) - 개발/디버깅용"""
    faiss_service.clear_index()
    return {
        "message": "FAISS index cleared",
        "total_in_index": faiss_service.get_total_count(),
    }


# ============ Event 관리 ============

@router.delete("/events/click")
def reset_click(
    user_id: str = Query(..., description="유저 UUID"),
    paper_id: int = Query(..., description="논문 ID"),
    db: Session = Depends(get_db),
):
    """특정 유저의 논문 클릭 기록 삭제 (click_count 초기화)"""
    db_user_id = get_user_id_from_uuid(db, user_id)

    stmt = select(UserEvent).where(
        and_(
            UserEvent.user_id == db_user_id,
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
    event_type: str = Query(None, description="특정 이벤트 타입만 삭제 (없으면 전체)"),
    db: Session = Depends(get_db),
):
    """특정 유저의 모든 이벤트 삭제"""
    db_user_id = get_user_id_from_uuid(db, user_id)

    stmt = select(UserEvent).where(UserEvent.user_id == db_user_id)
    if event_type:
        stmt = stmt.where(UserEvent.event_type == event_type)

    events = db.execute(stmt).scalars().all()
    count = len(events)

    for event in events:
        db.delete(event)
    db.commit()

    return {"message": f"Deleted {count} events", "user_id": user_id, "event_type": event_type}

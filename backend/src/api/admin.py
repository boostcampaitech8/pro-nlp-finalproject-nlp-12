"""Admin API - 시스템 관리 엔드포인트"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.mysql import get_db
from src.entity.paper import Paper
from src.service.faiss_service import faiss_service
from src.service.embedder_service import embed_texts

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

"""검색 API - FAISS 기반 논문 검색"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.repository.paper_repository import PaperRepository
from src.client.faiss_store import get_faiss_store
from src.client.embedder import embed_single
from src.config.settings import settings

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search_papers(
    q: str = Query(..., min_length=1, description="검색 쿼리"),
    k: int = Query(20, ge=1, le=100),
    user_id: str | None = Query(None, description="사용자 UUID (로깅용)"),
    db: Session = Depends(get_db),
):
    """
    FAISS 벡터 검색

    - 쿼리 텍스트를 임베딩하여 유사한 논문 검색
    """
    # 쿼리 임베딩
    query_vector = embed_single(q)

    # FAISS 검색
    faiss_store = get_faiss_store(
        dim=settings.EMBEDDING_DIM,
        index_path=settings.FAISS_INDEX_PATH + "/index.bin",
    )
    scores, ids = faiss_store.search(query_vector, k=k)

    # 유효한 ID만 필터링
    paper_ids = [int(pid) for pid in ids if pid >= 0]

    if not paper_ids:
        return {
            "user_id": user_id,
            "q": q,
            "k": k,
            "total": 0,
            "items": [],
        }

    # DB에서 논문 조회
    repo = PaperRepository(db)
    papers = repo.get_by_ids(paper_ids)

    # 검색 순서 유지
    paper_map = {p.id: p for p in papers}
    score_map = {int(ids[i]): float(scores[i]) for i in range(len(ids)) if ids[i] >= 0}

    items = []
    for pid in paper_ids:
        p = paper_map.get(pid)
        if not p:
            continue

        ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정
        items.append({
            "paper_id": p.id,
            "arxiv_id": p.arxiv_id,
            "title": p.title,
            "abstract": p.abstract,
            "published_date": p.published_date.isoformat() if p.published_date else None,
            "pdf_url": p.pdf_url,
            "score": score_map.get(pid, 0.0),
        })

    return {
        "user_id": user_id,
        "q": q,
        "k": k,
        "total": len(items),
        "items": items,
    }

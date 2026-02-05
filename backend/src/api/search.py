# app/routers/search.py
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.repository.paper_repo import PaperRepository

router = APIRouter()

@router.get("/search")
def search_papers(
    user_id: str = Query(...),
    q: str = Query(..., min_length=1),
    k: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    col = get_collection()  # chroma.py에 이미 있음

    res = col.query(
        query_texts=[q],
        n_results=k,
        include=["distances"],
    )

    ids = (res.get("ids") or [[]])[0]
    if not ids:
        return {"user_id": user_id, "q": q, "k": k, "total": 0, "items": []}

    paper_ids = []
    for s in ids:
        try:
            paper_ids.append(int(s))
        except Exception:
            continue

    repo = PaperRepository(db)
    papers = repo.get_by_ids(paper_ids)

    # 검색 순서 유지
    by_id = {p.id: p for p in papers}
    ordered = [by_id[i] for i in paper_ids if i in by_id]

    items = []
    for p in ordered:
        arxiv_id = getattr(p, "arxiv_id", None)
        abs_url = getattr(p, "abs_url", None)
        if abs_url is None and arxiv_id:
            abs_url = f"https://arxiv.org/abs/{arxiv_id}"

        published_at = getattr(p, "published_at", None) or getattr(p, "published_date", None)
        if published_at is not None:
            try:
                published_at = published_at.isoformat()
            except Exception:
                pass

        categories = None
        pcs = getattr(p, "paper_categories", None) or []
        cat_list = []
        for x in pcs:
            cat = getattr(x, "category", None)
            if cat is None:
                continue
            ct = getattr(cat, "category_type", None)
            if ct:
                cat_list.append(ct)
        if cat_list:
            categories = ", ".join(cat_list)

        items.append({
            "paper_id": getattr(p, "paper_id", None) or p.id,
            "id": p.id,
            "title": p.title,
            "abstract": p.abstract,
            "authors": getattr(p, "authors", None) or "",
            "categories": categories,
            "published_at": published_at,
            "year": getattr(p, "year", None),
            "arxiv_id": arxiv_id,
            "abs_url": abs_url,
            "pdf_url": getattr(p, "pdf_url", None),
        })

    return {"user_id": user_id, "q": q, "k": k, "total": len(items), "items": items}

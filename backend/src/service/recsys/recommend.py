from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, desc, and_

from src.service.recsys.cursor import decode_cursor, encode_cursor
from src.entity.summary import SummaryType


def recommend_page(
    *,
    db,
    user_id: str,
    limit: int,
    cursor: Optional[str],
    user_vec,
    event_repo,
    profile_repo,
    paper_model,
    summary_model,
    faiss_store,
    candidate_k: Optional[int] = None,
    pool_k: int = 80,
    seen_limit: int = 3000,
) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
    """
    - FAISS search로 paper_id 후보 추출
    - seen(impression) 제외하며 페이지 채움
    - DB에서 paper_id로 로드
    """

    eff_pool_k = int(candidate_k) if candidate_k is not None else int(pool_k)
    offset = decode_cursor(cursor)

    # FAISS search (k는 offset 고려해서 넉넉히)
    scores, ids = faiss_store.search(user_vec, k=max(eff_pool_k, limit + offset))

    # seen 제외용
    try:
        raw_seen = event_repo.get_seen_paper_ids(user_id, limit=seen_limit)
    except Exception:
        raw_seen = []

    seen_ids: set[int] = set()
    for x in raw_seen:
        try:
            seen_ids.add(int(x))
        except Exception:
            continue

    page_ids: List[int] = []
    page_scores: List[float] = []

    pos = offset
    while pos < len(ids) and len(page_ids) < limit:
        pid = int(ids[pos])
        sc = float(scores[pos])
        pos += 1

        if pid == -1:
            continue
        if pid in seen_ids:
            continue

        page_ids.append(pid)
        page_scores.append(sc)

    # DB 로드
    papers = _load_papers_by_ids(db=db, paper_model=paper_model, summary_model=summary_model, ids=page_ids)

    # order 유지
    paper_map = {int(getattr(p, "id")): p for p in papers if getattr(p, "id", None) is not None}

    items: List[Dict[str, Any]] = []
    for pid, sc in zip(page_ids, page_scores):
        p = paper_map.get(int(pid))
        if p is None:
            continue

        it = _paper_to_item(p, score=sc)

        # 좋아요/북마크 상태
        try:
            it["is_liked"] = event_repo.exists_event(user_id=user_id, paper_id=int(pid), event_type="like")
        except Exception:
            it["is_liked"] = False

        try:
            it["is_bookmarked"] = event_repo.exists_event(user_id=user_id, paper_id=int(pid), event_type="bookmark")
        except Exception:
            it["is_bookmarked"] = False

        items.append(it)

    has_more = pos < len(ids)
    next_cursor = encode_cursor(pos) if has_more else None
    return items, next_cursor, has_more


def fallback_page(
    *,
    db,
    user_id: str,
    limit: int,
    cursor: Optional[str],
    event_repo,
    profile_repo,
    paper_model,
    seen_limit: int = 3000,
    fetch_chunk: int = 50,
) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
    offset = decode_cursor(cursor)

    try:
        raw_seen = event_repo.get_seen_paper_ids(user_id, limit=seen_limit)
    except Exception:
        raw_seen = []

    seen_ids: set[int] = set()
    for x in raw_seen:
        try:
            seen_ids.add(int(x))
        except Exception:
            continue

    base_stmt = select(paper_model)
    if hasattr(paper_model, "published_at"):
        base_stmt = base_stmt.order_by(desc(getattr(paper_model, "published_at")))
    elif hasattr(paper_model, "published_date"):
        base_stmt = base_stmt.order_by(desc(getattr(paper_model, "published_date")))
    else:
        base_stmt = base_stmt.order_by(desc(getattr(paper_model, "id")))

    items: List[Dict[str, Any]] = []
    pos = offset

    while len(items) < limit:
        stmt = base_stmt.offset(pos).limit(fetch_chunk)
        rows = db.execute(stmt).scalars().all()
        if not rows:
            break

        for p in rows:
            pid_val = getattr(p, "id", None)
            try:
                pid_int = int(pid_val)
            except Exception:
                continue

            if pid_int in seen_ids:
                continue

            it = _paper_to_item(p, score=0.0)

            # 좋아요/북마크 상태
            try:
                it["is_liked"] = event_repo.exists_event(user_id=user_id, paper_id=int(pid_int), event_type="like")
            except Exception:
                it["is_liked"] = False

            try:
                it["is_bookmarked"] = event_repo.exists_event(user_id=user_id, paper_id=int(pid_int), event_type="bookmark")
            except Exception:
                it["is_bookmarked"] = False

            items.append(it)

            if len(items) >= limit:
                break

        pos += len(rows)
        if len(rows) < fetch_chunk:
            break

    has_more = len(items) >= limit
    next_cursor = encode_cursor(pos) if has_more else None
    return items, next_cursor, has_more


# [추가] Params: +summary_model
def _load_papers_by_ids(*, db, paper_model, summary_model, ids: List[int]):
    if not ids:
        return []
    
    # [수정] summary_text(keypoint)도 가져오게끔 수정
    stmt = (
        select(paper_model, summary_model.summary_text)
        .outerjoin(
            summary_model,
            and_(
                getattr(paper_model, "id") == summary_model.paper_id,
                summary_model.summary_type == SummaryType.keypoint.value
            )
        )
        .where(
            getattr(paper_model, "id").in_(ids),
        )
    )

    results = db.execute(stmt).all()

    # 데이터 가공
    papers = []
    for p_obj, summary_text in results:
        # Paper 객체에 임시로 summary 속성 할당
        setattr(p_obj, "summary", summary_text)
        papers.append(p_obj)

    order = {pid: i for i, pid in enumerate(ids)}
    papers.sort(key=lambda p: order.get(int(getattr(p, "id")), 10**9))
    return papers


def _paper_to_item(p, score: float):
    pid = getattr(p, "id", None)

    arxiv_id = getattr(p, "arxiv_id", None)
    abs_url = getattr(p, "abs_url", None)
    if abs_url is None and arxiv_id:
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"

    published_at = getattr(p, "published_at", None) or getattr(p, "published_date", None)
    published_at = published_at.isoformat() if published_at else None

    primary_category = None
    pc = getattr(p, "primary_category", None)
    if pc is not None:
        cat = getattr(pc, "category", None)
        if cat is not None:
            primary_category = getattr(cat, "category_type", None)

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

    return {
        "paper_id": int(pid) if pid is not None else None,
        "arxiv_id": arxiv_id,
        "title": getattr(p, "title", None),
        "pdf_url": getattr(p, "pdf_url", None),
        "abs_url": abs_url,
        "primary_category": primary_category,
        "categories": categories,
        "published_date": published_at,
        "summary": getattr(p, "summary", None),
    }

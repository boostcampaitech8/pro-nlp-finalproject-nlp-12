import json
import logging
from datetime import datetime
from typing import Dict, Iterable

import numpy as np

from src.client.embedder import embed_texts
from src.service.recsys.vector_utils import safe_l2_normalize

logger = logging.getLogger(__name__)

EVENT_WEIGHTS = {
    "view": 0.05,
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}

VECTOR_DIRTY_COOLDOWN_SEC = 60  # dirty flag 60초 타이머
ONBOARD_PRIMARY_WEIGHT = 1.0
ONBOARD_SECONDARY_WEIGHT = 0.4


def maybe_refresh_user_vector(*, user_id: str, profile_repo, event_repo, paper_repo, recent_limit: int = 120) -> None:
    prof = profile_repo.get(user_id)
    if prof is None:
        return

    dirty_at = getattr(prof, "vector_dirty_at", None)
    if dirty_at is None:
        return

    now = datetime.now(dirty_at.tzinfo) if getattr(dirty_at, "tzinfo", None) else datetime.utcnow()
    try:
        delta = (now - dirty_at).total_seconds()
    except Exception:
        logger.exception("Failed to compute vector dirty age for user_id=%s", user_id)
        return

    if delta < VECTOR_DIRTY_COOLDOWN_SEC:
        return

    evs = event_repo.get_recent_positive_events(user_id, limit=recent_limit)
    def _et_val(et):
        return getattr(et, "value", et)
    evs = [e for e in evs if _et_val(getattr(e, "event_type", None)) in ("bookmark", "like", "click")]
    if not evs:
        logger.info("User vector skip: no positive events user_id=%s", user_id)
        profile_repo.clear_vector_dirty(user_id)
        return

    w_map: Dict[int, float] = {}
    for e in evs:
        pid = getattr(e, "paper_id", None)
        if pid is None:
            continue
        et = _et_val(getattr(e, "event_type", None))
        w = float(EVENT_WEIGHTS.get(et, 0.0))
        try:
            pid_int = int(pid)
        except Exception:
            continue
        w_map[pid_int] = w_map.get(pid_int, 0.0) + w

    paper_ids = list(w_map.keys())
    papers = paper_repo.get_by_ids(paper_ids)
    if not papers:
        logger.info("User vector skip: no papers for events user_id=%s", user_id)
        profile_repo.clear_vector_dirty(user_id)
        return

    paper_map = {int(getattr(p, "id")): p for p in papers if getattr(p, "id", None) is not None}

    texts: list[str] = []
    ids: list[int] = []
    skipped_missing_paper = 0
    for pid in paper_ids:
        p = paper_map.get(pid)
        if not p:
            skipped_missing_paper += 1
            continue
        title = getattr(p, "title", "") or ""
        abstract = getattr(p, "abstract", "") or ""
        texts.append(f"Title: {title}\n\nAbstract: {abstract}")
        ids.append(pid)

    if not texts:
        logger.info("User vector skip: no texts user_id=%s missing_paper=%d", user_id, skipped_missing_paper)
        profile_repo.clear_vector_dirty(user_id)
        return

    try:
        vecs = embed_texts(texts)
    except Exception:
        logger.exception("User vector embed failed user_id=%s", user_id)
        profile_repo.clear_vector_dirty(user_id)
        return

    vec_sum = None
    w_sum = 0.0
    used = 0
    skipped_empty = 0
    skipped_shape = 0

    for pid, vec in zip(ids, vecs):
        w = w_map.get(pid, 0.0)
        if w <= 0:
            continue

        v = np.array(vec, dtype=float)
        if v.size == 0:
            skipped_empty += 1
            continue

        if vec_sum is None:
            vec_sum = np.zeros_like(v)
        if vec_sum.shape != v.shape:
            skipped_shape += 1
            profile_repo.clear_vector_dirty(user_id)
            return

        vec_sum += w * v
        w_sum += w
        used += 1

    if vec_sum is None or w_sum <= 0:
        logger.info(
            "User vector skip: no usable vectors user_id=%s used=%d missing_paper=%d skipped_empty=%d",
            user_id,
            used,
            skipped_missing_paper,
            skipped_empty,
        )
        profile_repo.clear_vector_dirty(user_id)
        return

    user_vec = vec_sum / w_sum
    user_vec = safe_l2_normalize(user_vec)

    profile_repo.upsert(user_id, json.dumps(user_vec.tolist()))
    logger.info(
        "User vector refreshed user_id=%s used=%d missing_paper=%d skipped_empty=%d",
        user_id,
        used,
        skipped_missing_paper,
        skipped_empty,
    )


def build_user_vector_from_categories(
    *,
    user_id: str,
    categories: Iterable[str],
    profile_repo,
    paper_repo,
    per_category_limit: int = 30,
    primary_weight: float = ONBOARD_PRIMARY_WEIGHT,
    secondary_weight: float = ONBOARD_SECONDARY_WEIGHT,
) -> bool:
    cats = [str(c).strip() for c in categories if str(c).strip()]
    if not cats:
        return False

    papers_by_id: Dict[int, object] = {}
    weights_by_id: Dict[int, float] = {}

    def _add_papers(papers, w: float):
        for p in papers:
            pid = getattr(p, "id", None)
            if pid is None:
                continue
            try:
                pid_int = int(pid)
            except Exception:
                continue
            if pid_int not in papers_by_id:
                papers_by_id[pid_int] = p
            weights_by_id[pid_int] = weights_by_id.get(pid_int, 0.0) + float(w)

    for cat in cats:
        try:
            prim = paper_repo.get_recent_papers_by_primary_category(cat, limit=per_category_limit)
        except Exception:
            prim = []
        _add_papers(prim, primary_weight)

        try:
            sec = paper_repo.get_recent_papers_by_any_category(cat, limit=per_category_limit)
        except Exception:
            sec = []
        _add_papers(sec, secondary_weight)

    if not papers_by_id:
        logger.info("Onboarding vector skip: no papers for categories user_id=%s", user_id)
        return False

    ids: list[int] = []
    texts: list[str] = []
    for pid, p in papers_by_id.items():
        title = getattr(p, "title", "") or ""
        abstract = getattr(p, "abstract", "") or ""
        texts.append(f"Title: {title}\n\nAbstract: {abstract}")
        ids.append(pid)

    try:
        vecs = embed_texts(texts)
    except Exception:
        logger.exception("Onboarding vector embed failed user_id=%s", user_id)
        return False

    vec_sum = None
    w_sum = 0.0
    used = 0

    for pid, vec in zip(ids, vecs):
        w = weights_by_id.get(pid, 0.0)
        if w <= 0:
            continue
        v = np.array(vec, dtype=float)
        if v.size == 0:
            continue

        if vec_sum is None:
            vec_sum = np.zeros_like(v)
        if vec_sum.shape != v.shape:
            return False

        vec_sum += w * v
        w_sum += w
        used += 1

    if vec_sum is None or w_sum <= 0:
        logger.info("Onboarding vector skip: no usable vectors user_id=%s used=%d", user_id, used)
        return False

    user_vec = safe_l2_normalize(vec_sum / w_sum)
    profile_repo.upsert(user_id, json.dumps(user_vec.tolist()))
    logger.info("Onboarding vector saved user_id=%s used=%d", user_id, used)
    return True

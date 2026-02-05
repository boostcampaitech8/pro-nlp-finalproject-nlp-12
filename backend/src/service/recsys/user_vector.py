import json
import numpy as np
from datetime import datetime
from typing import Dict

from src.service.recsys.vector_utils import safe_l2_normalize

EVENT_WEIGHTS = {
    "view": 0.05,
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}

VECTOR_DIRTY_COOLDOWN_SEC = 60


def maybe_refresh_user_vector(*, user_id: str, profile_repo, event_repo, faiss_store, recent_limit: int = 120) -> None:
    prof = profile_repo.get(user_id)
    if prof is None:
        return

    dirty_at = getattr(prof, "vector_dirty_at", None)
    if dirty_at is None:
        return

    now = datetime.utcnow()
    try:
        delta = (now - dirty_at).total_seconds()
    except Exception:
        return

    if delta < VECTOR_DIRTY_COOLDOWN_SEC:
        return

    evs = event_repo.get_recent_positive_events(user_id, limit=recent_limit)
    evs = [e for e in evs if getattr(e, "event_type", None) in ("bookmark", "like", "click")]
    if not evs:
        return

    # weight map (event_type 기반)
    w_map: Dict[int, float] = {}
    for e in evs:
        pid = getattr(e, "paper_id", None)
        if pid is None:
            continue
        et = getattr(e, "event_type", None)
        w = float(EVENT_WEIGHTS.get(et, 0.0))
        try:
            w_map[int(pid)] = w
        except Exception:
            w_map[int(pid)] = 0.0

    vec_sum = None
    w_sum = 0.0

    for pid, w in w_map.items():
        if w <= 0:
            continue
        try:
            emb = faiss_store.reconstruct(pid)  # ✅ paper_id로 벡터 재조회
        except Exception:
            continue

        v = np.array(emb, dtype=float)
        if v.size == 0:
            continue

        if vec_sum is None:
            vec_sum = np.zeros_like(v)
        if vec_sum.shape != v.shape:
            return

        vec_sum += w * v
        w_sum += w

    if vec_sum is None or w_sum <= 0:
        return

    user_vec = vec_sum / w_sum
    user_vec = safe_l2_normalize(user_vec)

    profile_repo.upsert(user_id, json.dumps(user_vec.tolist()))

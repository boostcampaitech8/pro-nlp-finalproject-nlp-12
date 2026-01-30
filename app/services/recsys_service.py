# app/services/recsys_service.py

import json
import base64
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.chroma import get_collection
from app.models.paper import Paper
from app.repositories.event_repo import EventRepository
from app.repositories.paper_repo import PaperRepository
from app.repositories.profile_repo import ProfileRepository


EVENT_WEIGHTS = {
    "view": 0.05,
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}

# dirty flag 쿨다운: 60초 지나고 feed 요청 들어오면 재계산
VECTOR_DIRTY_COOLDOWN_SEC = 60


def _encode_cursor(offset: int) -> str:
    raw = str(offset).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        return int(raw)
    except Exception:
        return 0


def _parse_vector_json(user_vector_json: Optional[str]) -> np.ndarray:
    if not user_vector_json:
        return np.array([], dtype=float)
    try:
        arr = json.loads(user_vector_json)
        if not isinstance(arr, list) or len(arr) == 0:
            return np.array([], dtype=float)
        return np.array(arr, dtype=float)
    except Exception:
        return np.array([], dtype=float)


def _get_category_attr() -> Optional[str]:
    for name in ["primary_category", "category", "categories"]:
        if hasattr(Paper, name):
            return name
    return None


def _get_pk_attr() -> Optional[str]:
    for name in ["paper_id", "id"]:
        if hasattr(Paper, name):
            return name
    return None


class RecSysService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.paper_repo = PaperRepository(db)
        self.profile_repo = ProfileRepository(db)

    def get_weight(self, event_type: str) -> float:
        if event_type not in EVENT_WEIGHTS:
            raise ValueError(
                f"Unknown event_type: {event_type}. Allowed: {list(EVENT_WEIGHTS.keys())}"
            )
        return float(EVENT_WEIGHTS[event_type])

    # =========================================================
    #  dirty_at + 60초 쿨다운 이후, feed 요청 시 벡터 재계산
    #   - 이벤트는 bookmark/like/click만 반영
    #   - 계산: 해당 논문 임베딩의 가중 평균
    #   - 저장: profile_repo.upsert() → vector_dirty_at = NULL 처리됨
    # =========================================================
    def _maybe_refresh_user_vector(
        self,
        *,
        user_id: str,
        collection_name: str = "papers_embed_v1",
        recent_limit: int = 120,
    ) -> None:
        prof = self.profile_repo.get(user_id)
        if prof is None:
            print("[vec] no profile", user_id)
            return

        dirty_at = getattr(prof, "vector_dirty_at", None)
        print("[vec] dirty_at:", dirty_at)
        if dirty_at is None:
            print("[vec] dirty_at is None -> skip")
            return

        now = datetime.utcnow()
        try:
            delta = (now - dirty_at).total_seconds()
        except Exception as e:
            print("[vec] dirty_at compare failed:", e, "type=", type(dirty_at))
            return

        print("[vec] delta_sec:", delta)
        if delta < VECTOR_DIRTY_COOLDOWN_SEC:
            print("[vec] cooldown not passed")
            return

        evs = self.event_repo.get_recent_positive_events(user_id, limit=recent_limit)
        evs = [e for e in evs if getattr(e, "event_type", None) in ("bookmark", "like", "click")]
        print("[vec] evs_count:", len(evs))
        if evs:
            print("[vec] evs_sample:", [(e.paper_id, e.event_type, getattr(e, "weight", None)) for e in evs[:10]])
        if not evs:
            print("[vec] no events -> skip")
            return

        ids = [str(e.paper_id) for e in evs if getattr(e, "paper_id", None) is not None]
        print("[vec] chroma_get_ids_sample:", ids[:10])
        if not ids:
            print("[vec] empty ids -> skip")
            return

        col = get_collection(collection_name)

        try:
            got = col.get(ids=ids, include=["embeddings"])
        except Exception as e:
            print("[vec] chroma get failed:", e)
            return

        ret_ids = got.get("ids")
        if ret_ids is None:
            ret_ids = []

        embs = got.get("embeddings")
        if embs is None:
            embs = []

        # numpy array / list 모두 안전 체크
        emb_len = None
        try:
            emb_len = len(embs)
        except Exception:
            try:
                emb_len = int(getattr(embs, "size"))
            except Exception:
                emb_len = 0

        print("[vec] chroma_ret_ids_sample:", ret_ids[:10])
        print("[vec] embeddings_len:", emb_len)

        if emb_len == 0:
            print("[vec] no embeddings returned -> skip (id mismatch likely)")
            return

        # weight map
        w_map: Dict[str, float] = {}
        for e in evs:
            try:
                w_map[str(e.paper_id)] = float(getattr(e, "weight", 0.0))
            except Exception:
                w_map[str(e.paper_id)] = 0.0

        vec_sum = None
        w_sum = 0.0

        for pid, emb in zip(ret_ids, embs):
            try:
                w = float(w_map.get(str(pid), 0.0))
            except Exception:
                w = 0.0
            if w <= 0:
                continue

            v = np.array(emb, dtype=float)
            if v.size == 0:
                continue

            if vec_sum is None:
                vec_sum = np.zeros_like(v)
            if vec_sum.shape != v.shape:
                print("[vec] embedding shape mismatch:", vec_sum.shape, v.shape)
                return

            vec_sum += w * v
            w_sum += w

        print("[vec] w_sum:", w_sum)
        if vec_sum is None or w_sum <= 0:
            print("[vec] vec_sum None or w_sum<=0 -> skip")
            return

        user_vec = vec_sum / w_sum

        try:
            norm = float(np.linalg.norm(user_vec))
            print("[vec] norm:", norm)
            if norm > 0:
                user_vec = user_vec / norm
        except Exception as e:
            print("[vec] norm failed:", e)

        self.profile_repo.upsert(user_id, json.dumps(user_vec.tolist()))
        print("[vec] saved user_vector_json, len:", len(user_vec))



    def recommend_page(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: Optional[str] = None,
        collection_name: str = "papers_embed_v1",
        # feed.py가 candidate_k로 넘겨도 받도록 호환
        candidate_k: Optional[int] = None,
        pool_k: int = 80,
        # 본 것 제외용 (feed.py에서 넘김)
        seen_limit: int = 3000,
        **_ignored_kwargs,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
        """
        빈 user_vector_json이면 Chroma query 금지 -> fallback으로.
        candidate_k가 오면 pool_k 대신 그 값을 사용.
        items에 score 포함
        본 것(seen=impression) 제외
        is_liked / is_bookmarked 주입
        dirty_at + 60초 → feed 요청 시 유저 벡터 재계산
        """
        eff_pool_k = int(candidate_k) if candidate_k is not None else int(pool_k)

        # 벡터 재계산 트리거
        self._maybe_refresh_user_vector(user_id=user_id, collection_name=collection_name)

        prof = self.profile_repo.get(user_id)
        user_vec = _parse_vector_json(
            getattr(prof, "user_vector_json", None) if prof else None
        )

        # Cold start: 벡터가 비어있으면 fallback
        if user_vec.size == 0:
            return self._fallback_page(user_id=user_id, limit=limit, cursor=cursor)

        offset = _decode_cursor(cursor)

        col = get_collection()
        res = col.query(
            query_embeddings=[user_vec.tolist()],
            n_results=max(eff_pool_k, limit + offset),
            include=["metadatas", "documents", "distances"],
        )

        ids = (res.get("ids") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]  # ✅ score 계산용

        # seen 제외: DB에서 온 paper_id가 str일 수도 있어서 int로 정규화
        try:
            raw_seen = self.event_repo.get_seen_paper_ids(user_id, limit=seen_limit)
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

        # offset부터 읽되, seen 제외하면서 limit개 채우기
        pos = offset
        while pos < len(ids) and len(page_ids) < limit:
            pid = ids[pos]
            meta = metas[pos]
            dist = dists[pos]
            pos += 1

            # dist -> score 변환
            try:
                score = 1.0 / (1.0 + float(dist))
            except Exception:
                score = 0.0

            # paper_id 해석 (meta 우선)
            if isinstance(meta, dict) and meta.get("paper_id") is not None:
                raw_pid = meta["paper_id"]
            else:
                raw_pid = pid

            try:
                pid_int = int(raw_pid)
            except Exception:
                continue

            if pid_int in seen_ids:
                continue

            page_ids.append(pid_int)
            page_scores.append(score)

        papers = self._load_papers_by_ids(page_ids)

        pk = _get_pk_attr()
        paper_map: Dict[int, Paper] = {}
        if pk:
            for p in papers:
                try:
                    paper_map[int(getattr(p, pk))] = p
                except Exception:
                    continue

        items: List[Dict[str, Any]] = []
        for pid, sc in zip(page_ids, page_scores):
            p = paper_map.get(int(pid))
            if p is None:
                continue

            it = self._paper_to_item(p, score=sc)

            # 좋아요/북마크 상태 주입
            try:
                it["is_liked"] = self.event_repo.exists_event(
                    user_id=user_id, paper_id=int(pid), event_type="like"
                )
            except Exception:
                it["is_liked"] = False

            try:
                it["is_bookmarked"] = self.event_repo.exists_event(
                    user_id=user_id, paper_id=int(pid), event_type="bookmark"
                )
            except Exception:
                it["is_bookmarked"] = False

            items.append(it)

        # next_cursor는 실제로 소비한 pos 기준
        has_more = pos < len(ids)
        next_cursor = _encode_cursor(pos) if has_more else None
        return items, next_cursor, has_more


    def _fallback_page(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: Optional[str],
        seen_limit: int = 3000,
        fetch_chunk: int = 50,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
        """
        Cold start fallback에서도 이미 본 것(impression) 제외
        - offset(cursor)부터 읽되, seen 제외하면서 limit개 채움
        - next_cursor는 실제로 소비한 pos 기준
        """
        offset = _decode_cursor(cursor)

        # seen(impression) ids
        try:
            raw_seen = self.event_repo.get_seen_paper_ids(user_id, limit=seen_limit)
        except Exception:
            raw_seen = []

        seen_ids: set[int] = set()
        for x in raw_seen:
            try:
                seen_ids.add(int(x))
            except Exception:
                continue

        # onboarding topics(기존 로직 유지)
        prof = self.profile_repo.get(user_id)
        topics = None
        if prof is not None:
            oj = getattr(prof, "onboarding_json", None)
            if isinstance(oj, dict):
                t = oj.get("topics")
                if isinstance(t, list) and len(t) > 0:
                    topics = t

        cat_attr = _get_category_attr()

        base_stmt = select(Paper)
        if topics and cat_attr:
            col = getattr(Paper, cat_attr)
            if cat_attr == "categories":
                base_stmt = base_stmt.where(col.like(f"%{topics[0]}%"))
            else:
                base_stmt = base_stmt.where(col.in_(topics))

        if hasattr(Paper, "published_at"):
            base_stmt = base_stmt.order_by(desc(getattr(Paper, "published_at")))
        else:
            pk = _get_pk_attr()
            if pk:
                base_stmt = base_stmt.order_by(desc(getattr(Paper, pk)))

        items: List[Dict[str, Any]] = []
        pos = offset

        while len(items) < limit:
            stmt = base_stmt.offset(pos).limit(fetch_chunk)
            rows = self.db.execute(stmt).scalars().all()
            if not rows:
                break

            pk = _get_pk_attr()

            for p in rows:
                pid_val = getattr(p, pk, None) if pk else None
                try:
                    pid_int = int(pid_val)
                except Exception:
                    continue

                if pid_int in seen_ids:
                    continue

                items.append(self._paper_to_item(p, score=0.0))
                if len(items) >= limit:
                    break

            pos += len(rows)

            if len(rows) < fetch_chunk:
                break

        has_more = len(items) >= limit
        next_cursor = _encode_cursor(pos) if has_more else None
        return items, next_cursor, has_more


    def _load_papers_by_ids(self, ids: List[Any]) -> List[Paper]:
        pk = _get_pk_attr()
        if not ids or not pk:
            return []

        cleaned: List[int] = []
        for x in ids:
            try:
                cleaned.append(int(x))
            except Exception:
                continue

        if not cleaned:
            return []

        stmt = select(Paper).where(getattr(Paper, pk).in_(cleaned))
        papers = self.db.execute(stmt).scalars().all()

        order = {pid: i for i, pid in enumerate(cleaned)}
        papers.sort(key=lambda p: order.get(getattr(p, pk), 10**9))
        return papers

    def _paper_to_item(self, p: Paper, score: Optional[float] = None) -> Dict[str, Any]:
        pk = _get_pk_attr()
        paper_id_val = getattr(p, pk, None) if pk else None

        return {
            "paper_id": int(paper_id_val) if paper_id_val is not None else None,
            "score": float(score) if score is not None else 0.0,
            "arxiv_id": getattr(p, "arxiv_id", None),
            "title": getattr(p, "title", None),
            "abstract": getattr(p, "abstract", None),
            "authors": getattr(p, "authors", None),
            "primary_category": getattr(p, "primary_category", None),
            "categories": getattr(p, "categories", None),
            "published_at": getattr(p, "published_at", None).isoformat()
            if getattr(p, "published_at", None)
            else None,
            "abs_url": getattr(p, "abs_url", None),
            "pdf_url": getattr(p, "pdf_url", None),
        }

"""빠른 추천 서비스 (유저 벡터 기반)"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
import numpy as np

from src.entity.paper import Paper
from src.entity.user_event import EventType
from src.repository.event_repository import EventRepository
from src.repository.paper_repository import PaperRepository
from src.repository.user_repository import UserRepository
from src.client.faiss_store import get_faiss_store
from src.config.settings import settings
from src.utils.cursor import encode_cursor, decode_cursor
from src.utils.vector_utils import parse_vector_json, safe_l2_normalize

logger = logging.getLogger(__name__)

# 이벤트 가중치
EVENT_WEIGHTS = {
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}

# 벡터 갱신 쿨다운 (초)
VECTOR_DIRTY_COOLDOWN_SEC = 60


class FeedService:
    """빠른 추천 서비스 - 유저 벡터 DB 저장 방식"""

    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.paper_repo = PaperRepository(db)
        self.user_repo = UserRepository(db)
        self.faiss = get_faiss_store(
            dim=settings.EMBEDDING_DIM,
            index_path=settings.FAISS_INDEX_PATH + "/index.bin"
        )

    def get_weight(self, event_type: str) -> float:
        """이벤트 타입별 가중치 반환"""
        if event_type not in EVENT_WEIGHTS:
            raise ValueError(f"Unknown event_type: {event_type}")
        return float(EVENT_WEIGHTS[event_type])

    def recommend_feed(
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        pool_k: int = 80,
        seen_limit: int = 3000,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
        """
        추천 피드 생성

        Args:
            user_id: 사용자 UUID
            limit: 반환할 개수
            cursor: 페이지네이션 커서
            pool_k: FAISS 검색 후보 수
            seen_limit: seen 체크 제한

        Returns:
            (items, next_cursor, has_more)
        """
        # 유저 확인 및 벡터 갱신
        user = self.user_repo.ensure_user(user_id)
        self._maybe_refresh_user_vector(user_id)

        # 유저 벡터 로드
        user = self.user_repo.get_by_uuid(user_id)
        user_vec = parse_vector_json(user.user_vector_json if user else None)

        # Cold start: 벡터 없으면 fallback
        if user_vec.size == 0:
            return self._fallback_feed(user_id, limit, cursor, seen_limit)

        return self._recommend_feed(
            user_id=user_id,
            user_vec=user_vec,
            limit=limit,
            cursor=cursor,
            pool_k=pool_k,
            seen_limit=seen_limit,
        )

    def _recommend_feed(
        self,
        user_id: str,
        user_vec: np.ndarray,
        limit: int,
        cursor: Optional[str],
        pool_k: int,
        seen_limit: int,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
        """FAISS 기반 추천"""
        offset = decode_cursor(cursor)

        # FAISS 검색
        scores, ids = self.faiss.search(user_vec, k=max(pool_k, limit + offset))

        # seen 논문 제외
        user = self.user_repo.get_by_uuid(user_id)
        seen_ids = self.event_repo.get_seen_paper_ids(user.id, limit=seen_limit) if user else set()

        page_ids: List[int] = []
        page_scores: List[float] = []

        pos = offset
        while pos < len(ids) and len(page_ids) < limit:
            pid = int(ids[pos])
            sc = float(scores[pos])
            pos += 1

            if pid == -1 or pid in seen_ids:
                continue

            page_ids.append(pid)
            page_scores.append(sc)

        # DB에서 논문 정보 로드
        papers = self.paper_repo.get_by_ids(page_ids)
        paper_map = {p.id: p for p in papers}

        items = []
        for pid, sc in zip(page_ids, page_scores):
            p = paper_map.get(pid)
            if not p:
                continue

            item = self._paper_to_item(p, score=sc)

            # 좋아요/북마크 상태
            if user:
                item["is_liked"] = self.event_repo.exists_event(user.id, pid, EventType.like)
                item["is_bookmarked"] = self.event_repo.exists_event(user.id, pid, EventType.bookmark)

            items.append(item)

        has_more = pos < len(ids)
        next_cursor = encode_cursor(pos) if has_more else None
        return items, next_cursor, has_more

    def _fallback_feed(
        self,
        user_id: str,
        limit: int,
        cursor: Optional[str],
        seen_limit: int,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
        """Cold start용 최신 논문 피드"""
        offset = decode_cursor(cursor)

        user = self.user_repo.get_by_uuid(user_id)
        seen_ids = self.event_repo.get_seen_paper_ids(user.id, limit=seen_limit) if user else set()

        # 최신 논문 조회
        stmt = select(Paper).order_by(desc(Paper.published_date))

        items = []
        pos = offset
        fetch_chunk = 50

        while len(items) < limit:
            rows = self.db.execute(stmt.offset(pos).limit(fetch_chunk)).scalars().all()
            if not rows:
                break

            for p in rows:
                if p.id in seen_ids:
                    continue
                items.append(self._paper_to_item(p, score=0.0))
                if len(items) >= limit:
                    break

            pos += len(rows)
            if len(rows) < fetch_chunk:
                break

        has_more = len(items) >= limit
        next_cursor = encode_cursor(pos) if has_more else None
        return items, next_cursor, has_more

    def _maybe_refresh_user_vector(self, user_id: str) -> None:
        """dirty flag 기반 유저 벡터 갱신"""
        user = self.user_repo.get_by_uuid(user_id)
        if not user or not user.vector_dirty_at:
            return

        # 쿨다운 체크
        delta = (datetime.utcnow() - user.vector_dirty_at).total_seconds()
        if delta < VECTOR_DIRTY_COOLDOWN_SEC:
            return

        # 최근 긍정 이벤트 조회
        evs = self.event_repo.get_recent_positive_events(user.id, limit=120)
        evs = [e for e in evs if e.event_type in (EventType.bookmark, EventType.like, EventType.click)]

        if not evs:
            return

        # 가중 평균 벡터 계산
        vec_sum = None
        w_sum = 0.0

        for e in evs:
            # event_type별 가중치 (e.event_type.value = "like", "bookmark", etc.)
            w = EVENT_WEIGHTS.get(e.event_type.value, 0.0)
            if w <= 0:
                continue

            try:
                emb = self.faiss.reconstruct(e.paper_id)
            except Exception:
                continue

            v = np.array(emb, dtype=float)
            if v.size == 0:
                continue

            if vec_sum is None:
                vec_sum = np.zeros_like(v)

            vec_sum += w * v
            w_sum += w

        if vec_sum is None or w_sum <= 0:
            return

        user_vec = vec_sum / w_sum
        user_vec = safe_l2_normalize(user_vec)

        # DB 저장
        self.user_repo.upsert_vector(user_id, json.dumps(user_vec.tolist()))

    def _paper_to_item(self, p: Paper, score: float) -> Dict[str, Any]:
        """Paper 엔티티를 응답 딕셔너리로 변환"""
        ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정 (primary_category, categories, abs_url 제거)
        return {
            "paper_id": p.id,
            "arxiv_id": p.arxiv_id,
            "title": p.title,
            "abstract": p.abstract,
            "published_date": p.published_date.isoformat() if p.published_date else None,
            "pdf_url": p.pdf_url,
            "citation_count": p.citation_count or 0,
            "score": float(score),
            "is_liked": False,
            "is_bookmarked": False,
        }

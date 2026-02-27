from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config import settings
from src.entity.paper import Paper
from src.entity.summary import Summary
from src.repository.event_repo import EventRepository
from src.repository.paper_repo import PaperRepository
from src.repository.profile_repo import ProfileRepository

from src.client.faiss_store import get_faiss_store
from src.service.recsys.vector_utils import parse_vector_json
from src.service.recsys.user_vector import maybe_refresh_user_vector
from src.service.recsys.recommend import recommend_page, fallback_page


EVENT_WEIGHTS = {
    "view": 0.05,
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}


class RecSysService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
        self.paper_repo = PaperRepository(db)
        self.profile_repo = ProfileRepository(db)

        # ✅ 하드코딩 제거: settings로 통일
        self.faiss = get_faiss_store()

    def get_weight(self, event_type: str) -> float:
        """
        events API에서 사용. 이벤트 타입별 가중치 정책은 여기서 단일 관리.
        """
        if event_type not in EVENT_WEIGHTS:
            raise ValueError(f"Unknown event_type: {event_type}. Allowed: {list(EVENT_WEIGHTS.keys())}")
        return float(EVENT_WEIGHTS[event_type])

    def recommend_page(
        self,
        *,
        user_id: str,
        limit: int,
        cursor: Optional[str] = None,
        candidate_k: Optional[int] = None,
        pool_k: int = 80,
        seen_limit: int = 3000,
        **_ignored_kwargs,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
        # dirty flag 기반 유저 벡터 갱신 (FAISS reconstruct 사용)
        maybe_refresh_user_vector(
            user_id=user_id,
            profile_repo=self.profile_repo,
            event_repo=self.event_repo,
            paper_repo=self.paper_repo,
        )

        prof = self.profile_repo.get(user_id)
        user_vec = parse_vector_json(
            getattr(prof, "user_vector_json", None) if prof else None
        )

        # cold start
        if user_vec.size == 0:
            return fallback_page(
                db=self.db,
                user_id=user_id,
                limit=limit,
                cursor=cursor,
                event_repo=self.event_repo,
                profile_repo=self.profile_repo,
                paper_model=Paper,
                seen_limit=seen_limit,
            )

        return recommend_page(
            db=self.db,
            user_id=user_id,
            limit=limit,
            cursor=cursor,
            user_vec=user_vec,
            event_repo=self.event_repo,
            profile_repo=self.profile_repo,
            paper_model=Paper,
            summary_model=Summary,
            faiss_store=self.faiss,
            candidate_k=candidate_k,
            pool_k=pool_k,
            seen_limit=seen_limit,
        )

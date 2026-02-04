"""느린 추천 서비스 (LLM 실시간 쿼리 기반)"""
import json
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import numpy as np

from src.entity.paper import Paper
from src.entity.user import User
from src.client.embedder import embed_single
from src.client.faiss_store import get_faiss_store
from src.config.settings import settings
from src.repository.paper_repository import PaperRepository
from src.repository.user_repository import UserRepository
from src.repository.event_repository import EventRepository

logger = logging.getLogger(__name__)

# 이벤트 가중치
EVENT_WEIGHTS = {
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}

# 점수 계산 가중치
ALPHA = 0.4   # 벡터 유사도
BETA = 0.15   # 키워드 매칭
GAMMA = 0.15  # 최신성
DELTA = 0.3   # 소스 가중치

SOURCE_WEIGHTS = {
    "faiss": 1.0,
    "arxiv": 0.6,
    "category": 0.2,
}


### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정 (primary_category, categories, abs_url 제거)
@dataclass
class Candidate:
    """추천 후보 논문"""
    paper_id: int
    arxiv_id: str
    title: str
    abstract: str
    published_date: Optional[str]
    pdf_url: Optional[str]
    citation_count: int
    source: str
    raw_score: float
    final_score: float = 0.0


class RecommendService:
    """느린 추천 서비스 - LLM 실시간 쿼리 방식"""

    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.user_repo = UserRepository(db)
        self.event_repo = EventRepository(db)
        self.faiss = get_faiss_store(
            dim=settings.EMBEDDING_DIM,
            index_path=settings.FAISS_INDEX_PATH + "/index.bin"
        )

    def get_user_profile(self, user_id: str) -> Optional[User]:
        """사용자 프로필 조회"""
        return self.user_repo.get_by_uuid(user_id)

    def get_onboarding_data(self, user_id: str) -> Optional[dict]:
        """온보딩 데이터 조회"""
        user = self.get_user_profile(user_id)
        if user and user.onboarding_json:
            return user.onboarding_json
        return None

    def get_seen_paper_ids(self, user_id: str, limit: int = 1000) -> set[int]:
        """사용자가 본 논문 ID 조회 (dislike만 제외)"""
        user = self.user_repo.get_by_uuid(user_id)
        if not user:
            return set()
        # dislike 이벤트만 제외 (like/bookmark는 다시 표시 가능)
        from src.entity.user_event import EventType
        paper_ids = self.event_repo.get_interacted_paper_ids(user.id, event_types=[EventType.impression])
        return set(paper_ids)

    def recommend(
        self,
        user_id: str,
        k: int = 30,
        use_faiss: bool = True,
        use_category: bool = True,
    ) -> dict:
        """
        LLM 기반 통합 추천

        Args:
            user_id: 사용자 UUID
            k: 추천할 논문 수
            use_faiss: FAISS 벡터 검색 사용
            use_category: 카테고리 기반 검색 사용

        Returns:
            {
                "items": [...],
                "sources_used": [...],
                "cold_start": bool,
                "timings": {...}
            }
        """
        total_start = time.time()
        timings = {}

        # 사용자 정보 로드
        t0 = time.time()
        user = self.get_user_profile(user_id)
        onboarding = self.get_onboarding_data(user_id)
        timings["profile_load"] = round(time.time() - t0, 3)

        # Cold Start: 온보딩 미완료
        if not user or not user.has_onboarded:
            logger.warning(f"Cold start for user {user_id} - not onboarded")
            return {
                "items": [],
                "sources_used": [],
                "cold_start": True,
                "timings": timings,
            }

        # 키워드/카테고리 추출
        keywords = onboarding.get("keywords", []) if onboarding else []
        categories = onboarding.get("categories", []) if onboarding else []

        # Preference Query 생성 및 임베딩
        t0 = time.time()
        preference_query = self._build_preference_query(categories, keywords)
        query_vector = embed_single(preference_query)
        timings["query_embedding"] = round(time.time() - t0, 3)

        candidates: List[Candidate] = []
        sources_used = []

        # seen_ids 로드
        t0 = time.time()
        seen_ids = self.get_seen_paper_ids(user_id)
        timings["seen_ids_load"] = round(time.time() - t0, 3)

        # [1] FAISS 벡터 검색
        if use_faiss:
            t0 = time.time()
            faiss_results = self._search_faiss(query_vector, n=100)
            timings["faiss_search"] = round(time.time() - t0, 3)
            candidates.extend(faiss_results)
            if faiss_results:
                sources_used.append("faiss")
            logger.info(f"FAISS search: {len(faiss_results)} results")

        # [2] 카테고리 기반 검색 (fallback)
        if use_category:
            t0 = time.time()
            cat_results = self._search_recent(exclude_ids=seen_ids, n=50)
            timings["category_search"] = round(time.time() - t0, 3)
            candidates.extend(cat_results)
            if cat_results:
                sources_used.append("category")

        # 병합 + 점수 계산
        t0 = time.time()
        merged = self._merge_and_score(candidates, keywords, seen_ids)
        timings["merge_score"] = round(time.time() - t0, 3)

        ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정 (primary_category, categories, abs_url 제거)
        # 응답 형식화
        items = [
            {
                "paper_id": c.paper_id,
                "arxiv_id": c.arxiv_id,
                "title": c.title,
                "abstract": c.abstract,
                "published_date": c.published_date,
                "pdf_url": c.pdf_url,
                "citation_count": c.citation_count,
                "score": round(c.final_score, 4),
                "source": c.source,
            }
            for c in merged[:k]
        ]

        timings["total"] = round(time.time() - total_start, 3)
        logger.info(f"Total recommend: {timings['total']}s")

        return {
            "items": items,
            "sources_used": list(set(sources_used)),
            "cold_start": False,
            "timings": timings,
        }

    def _build_preference_query(self, categories: List[str], keywords: List[str]) -> str:
        """Preference Query 텍스트 생성"""
        categories_text = ", ".join(categories) if categories else "general"
        keywords_text = ", ".join(keywords) if keywords else "research papers"

        return f"""
        Categories of interest: {categories_text}
        Research topics and keywords: {keywords_text}
        """

    def _search_faiss(self, query_vector: np.ndarray, n: int = 100) -> List[Candidate]:
        """FAISS 벡터 검색"""
        try:
            scores, ids = self.faiss.search(query_vector, k=n)

            paper_ids = [int(pid) for pid in ids if pid >= 0]
            if not paper_ids:
                return []

            # DB에서 메타데이터 조회
            papers = self.paper_repo.get_by_ids(paper_ids)
            paper_map = {p.id: p for p in papers}

            candidates = []
            for i, pid in enumerate(paper_ids):
                p = paper_map.get(pid)
                if not p:
                    continue

                # 점수 정규화
                raw = float(scores[i]) if i < len(scores) else 0.5
                normalized_score = min(1.0, max(0.5, 0.5 + (raw - 0.3) * 1.25))

                ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정
                candidates.append(Candidate(
                    paper_id=p.id,
                    arxiv_id=p.arxiv_id,
                    title=p.title,
                    abstract=p.abstract or "",
                    published_date=p.published_date.isoformat() if p.published_date else None,
                    pdf_url=p.pdf_url,
                    citation_count=p.citation_count or 0,
                    source="faiss",
                    raw_score=normalized_score,
                ))

            return candidates

        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []

    def _search_recent(self, exclude_ids: set[int], n: int = 50) -> List[Candidate]:
        """최신 논문 조회 (fallback)"""
        try:
            papers = self.paper_repo.get_recent_papers(limit=n + len(exclude_ids))

            candidates = []
            count = 0
            for p in papers:
                if p.id in exclude_ids:
                    continue
                if count >= n:
                    break

                score = 0.5 - (count / n) * 0.2

                ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정
                candidates.append(Candidate(
                    paper_id=p.id,
                    arxiv_id=p.arxiv_id,
                    title=p.title,
                    abstract=p.abstract or "",
                    published_date=p.published_date.isoformat() if p.published_date else None,
                    pdf_url=p.pdf_url,
                    citation_count=p.citation_count or 0,
                    source="category",
                    raw_score=score,
                ))
                count += 1

            return candidates

        except Exception as e:
            logger.error(f"Recent papers search error: {e}")
            return []

    def _merge_and_score(
        self,
        candidates: List[Candidate],
        keywords: List[str],
        seen_ids: set[int],
    ) -> List[Candidate]:
        """후보 병합 및 최종 스코어 계산"""
        # arxiv_id 기준 중복 제거
        seen_arxiv: Dict[str, Candidate] = {}
        for c in candidates:
            if c.paper_id in seen_ids:
                continue

            key = c.arxiv_id
            if key not in seen_arxiv or c.raw_score > seen_arxiv[key].raw_score:
                seen_arxiv[key] = c

        unique = list(seen_arxiv.values())

        # 최종 스코어 계산
        for item in unique:
            recency = self._calc_recency(item.published_date)
            kw_score = self._calc_keyword_score(item, keywords)
            source_w = SOURCE_WEIGHTS.get(item.source, 0.5)

            item.final_score = (
                ALPHA * item.raw_score +
                BETA * kw_score +
                GAMMA * recency +
                DELTA * source_w
            )

        unique.sort(key=lambda x: x.final_score, reverse=True)
        return unique

    def _calc_recency(self, published_date: Optional[str]) -> float:
        """최신성 점수 (0.0 ~ 1.0)"""
        if not published_date:
            return 0.5
        try:
            if "T" in published_date:
                pub = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            else:
                pub = datetime.fromisoformat(published_date)

            days = (datetime.now(pub.tzinfo) - pub).days
            return max(0.0, 1.0 - days / 365)
        except:
            return 0.5

    def _calc_keyword_score(self, item: Candidate, keywords: List[str]) -> float:
        """키워드 매칭 점수 (0.0 ~ 1.0)"""
        if not keywords:
            return 0.5

        text = (item.title + " " + item.abstract).lower()
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return min(1.0, matches / max(len(keywords), 1))

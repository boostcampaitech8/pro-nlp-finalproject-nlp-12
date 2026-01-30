"""추천 엔진 서비스 - 사용자에게 개인화된 논문 추천 (MVp2 호환성 재구현)"""
import json
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_
import numpy as np

from src.entity.paper import Paper
from src.entity.user import User
from src.entity.user_event import UserEvent
from src.service.embedder_service import embed_single
from src.service.faiss_service import faiss_service
from src.config.settings import settings
from src.repository.paper_repository import PaperRepository
from src.repository.user_profile_repository import UserProfileRepository
from src.repository.user_event_repository import UserEventRepository

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
ALPHA = 0.4   # 벡터 유사도 (정규화된 raw_score)
BETA = 0.15   # 키워드 매칭
GAMMA = 0.15  # 최신성
DELTA = 0.3   # 소스 가중치

SOURCE_WEIGHTS = {
    "faiss": 1.0,     # DB 유사도 검색 - 가장 정확
    "arxiv": 0.6,     # 실시간 검색 - 최신 논문 보완
    "category": 0.2,  # fallback - FAISS/arxiv 부족 시에만
}


@dataclass
class Candidate:
    """추천 후보 논문"""
    paper_id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: Optional[str]
    published_at: Optional[str]
    abs_url: Optional[str]
    pdf_url: Optional[str]
    source: str
    raw_score: float
    final_score: float = 0.0


class RecommendService:
    """개인화 추천 서비스 - MVp2 호환성 유지"""
    
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.profile_repo = UserProfileRepository(db)
        self.event_repo = UserEventRepository(db)
    
    def get_profile(self, user_id: str) -> Optional[User]:
        """사용자 프로필 조회"""
        return self.profile_repo.get_by_user_id(user_id)
    
    def get_categories(self, user_id: str) -> list[str]:
        """사용자 카테고리 조회"""
        profile = self.get_profile(user_id)
        if profile and profile.survey_categories:
            try:
                return json.loads(profile.survey_categories)
            except:
                pass
        return []
    
    def get_keywords(self, user_id: str) -> list[str]:
        """사용자 추출 키워드 조회"""
        profile = self.get_profile(user_id)
        if profile and profile.extracted_keywords:
            try:
                return json.loads(profile.extracted_keywords)
            except:
                pass
        return []
    
    def get_user_vector(self, user_id: str) -> Optional[np.ndarray]:
        """사용자 선호도 벡터 조회"""
        profile = self.get_profile(user_id)
        if profile and profile.user_vector_json:
            try:
                vector = json.loads(profile.user_vector_json)
                return np.array(vector, dtype=np.float32)
            except:
                pass
        return None
    
    def get_seen_paper_ids(self, user_id: str, limit: int = 1000) -> set[int]:
        """
        사용자가 본 논문 ID 조회 (dislike만 제외, like/bookmark는 다시 표시)
        """
        paper_ids = self.event_repo.get_interacted_paper_ids(user_id, event_types=["dislike"])
        return set(paper_ids)
    
    def recommend(
        self,
        user_id: str,
        k: int = 30,
        use_faiss: bool = True,
        use_arxiv: bool = True,
        use_category: bool = True,
    ) -> dict:
        """
        통합 추천 엔진
        
        Args:
            user_id: 사용자 ID
            k: 추천할 논문 수
            use_faiss: FAISS 벡터 검색 사용
            use_arxiv: arXiv 실시간 검색 사용
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
        categories = self.get_categories(user_id)
        keywords = self.get_keywords(user_id)
        user_vector = self.get_user_vector(user_id)
        timings["profile_load"] = round(time.time() - t0, 3)
        
        # Cold Start 감지: 설문 미완료 (user_vector 없음)
        if user_vector is None:
            logger.warning(f"Cold start for user {user_id} - no preference vector")
            return {
                "items": [],
                "sources_used": [],
                "cold_start": True,
                "timings": timings,
            }
        
        candidates: list[Candidate] = []
        sources_used = []
        
        # seen_ids 로드 (dislike만 제외)
        t0 = time.time()
        seen_ids = self.get_seen_paper_ids(user_id)
        timings["seen_ids_load"] = round(time.time() - t0, 3)
        
        # [1] FAISS 벡터 검색
        if use_faiss and user_vector is not None:
            t0 = time.time()
            faiss_results = self._search_faiss(user_vector, n=100)
            timings["faiss_search"] = round(time.time() - t0, 3)
            candidates.extend(faiss_results)
            if faiss_results:
                sources_used.append("faiss")
            logger.info(f"FAISS search: {len(faiss_results)} results in {timings['faiss_search']}s")
        
        # [2] arXiv 실시간 검색 (현재는 구현 미정)
        if use_arxiv and (keywords or categories):
            t0 = time.time()
            # arXiv 검색은 별도 ArxivService 필요 (현재 paper_v5에서는 구현 안함)
            # arxiv_results = self._search_arxiv(keywords, categories, n=50)
            # candidates.extend(arxiv_results)
            # if arxiv_results:
            #     sources_used.append("arxiv")
            timings["arxiv_search"] = round(time.time() - t0, 3)
        
        # [3] 카테고리 기반 검색
        if use_category:
            t0 = time.time()
            cat_results = self._search_recent(exclude_ids=seen_ids, n=50)
            timings["category_search"] = round(time.time() - t0, 3)
            candidates.extend(cat_results)
            if cat_results:
                sources_used.append("category")
            logger.info(f"Category search: {len(cat_results)} results in {timings['category_search']}s")
        
        # 병합 + 점수 계산
        t0 = time.time()
        merged = self._merge_and_score(candidates, keywords, seen_ids)
        timings["merge_score"] = round(time.time() - t0, 3)
        
        # 응답 형식화
        items = [
            {
                "paper_id": c.paper_id,
                "arxiv_id": c.arxiv_id,
                "title": c.title,
                "abstract": c.abstract,
                "authors": c.authors,
                "primary_category": c.primary_category,
                "categories": c.categories,
                "published_at": c.published_at,
                "abs_url": c.abs_url,
                "pdf_url": c.pdf_url,
                "score": round(c.final_score, 4),
                "source": c.source,
            }
            for c in merged[:k]
        ]
        
        timings["total"] = round(time.time() - total_start, 3)
        logger.info(f"Total recommend: {timings['total']}s | Breakdown: {timings}")
        
        return {
            "items": items,
            "sources_used": list(set(sources_used)),
            "cold_start": False,
            "timings": timings,
        }
    
    def _search_faiss(self, user_vector: np.ndarray, n: int = 100) -> list[Candidate]:
        """FAISS 벡터 검색"""
        try:
            results = faiss_service.search(user_vector, k=n)
            if not results or not isinstance(results, tuple):
                return []
            
            distances, indices = results
            paper_ids = [int(idx) for idx in indices if idx >= 0]
            
            if not paper_ids:
                return []
            
            # DB에서 메타데이터 조회
            papers_list = self.paper_repo.get_by_ids(paper_ids)
            papers = {p.id: p for p in papers_list}
            
            candidates = []
            for i, idx in enumerate(indices):
                if idx < 0:
                    continue
                
                idx = int(idx)
                p = papers.get(idx)
                if not p:
                    continue
                
                # FAISS 거리 정규화: [0.3, 0.7] → [0.5, 1.0]
                raw = 1.0 / (1.0 + distances[i]) if i < len(distances) else 0.5
                normalized_score = min(1.0, max(0.5, 0.5 + (raw - 0.3) * 1.25))
                
                candidates.append(Candidate(
                    paper_id=int(p.id),
                    arxiv_id=p.arxiv_id,
                    title=p.title,
                    abstract=p.abstract or "",
                    authors=None,
                    published_at=p.published_date.isoformat() if p.published_date else None,
                    abs_url=f"https://arxiv.org/abs/{p.arxiv_id}",
                    pdf_url=p.pdf_url,
                    source="faiss",
                    raw_score=normalized_score,
                ))
            
            return candidates
        
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []
    
    def _search_recent(
        self,
        exclude_ids: set[int],
        n: int = 50
    ) -> list[Candidate]:
        """최신 논문 조회 (카테고리 기반 fallback)"""
        try:
            # Repository에서 최신 논문 조회
            papers = self.paper_repo.get_recent_papers(limit=n + len(exclude_ids))
            
            candidates = []
            count = 0
            for p in papers:
                if p.id in exclude_ids:
                    continue
                if count >= n:
                    break
                
                # category(fallback) 점수: [0.3, 0.5] 범위
                score = 0.5 - (count / n) * 0.2
                
                candidates.append(Candidate(
                    paper_id=int(p.id),
                    arxiv_id=p.arxiv_id,
                    title=p.title,
                    abstract=p.abstract or "",
                    authors=None,
                    published_at=p.published_date.isoformat() if p.published_date else None,
                    abs_url=f"https://arxiv.org/abs/{p.arxiv_id}",
                    pdf_url=p.pdf_url,
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
        candidates: list[Candidate],
        keywords: list[str],
        seen_ids: set[int],
    ) -> list[Candidate]:
        """후보 병합 및 최종 스코어 계산"""
        # arxiv_id 기준 중복 제거
        seen_arxiv: dict[str, Candidate] = {}
        for c in candidates:
            # dislike 제외
            if c.paper_id > 0 and c.paper_id in seen_ids:
                continue
            
            key = c.arxiv_id
            if key not in seen_arxiv or c.raw_score > seen_arxiv[key].raw_score:
                seen_arxiv[key] = c
        
        unique = list(seen_arxiv.values())
        
        # 최종 스코어 계산
        for item in unique:
            recency = self._calc_recency(item.published_at)
            kw_score = self._calc_keyword_score(item, keywords)
            source_w = SOURCE_WEIGHTS.get(item.source, 0.5)
            
            item.final_score = (
                ALPHA * item.raw_score +
                BETA * kw_score +
                GAMMA * recency +
                DELTA * source_w
            )
        
        # 최종 스코어 순 정렬
        unique.sort(key=lambda x: x.final_score, reverse=True)
        return unique
    
    def _calc_recency(self, published_at: Optional[str]) -> float:
        """최신성 점수 계산 (0.0 ~ 1.0)"""
        if not published_at:
            return 0.5
        try:
            if "T" in published_at:
                pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            else:
                pub = datetime.fromisoformat(published_at)
            
            days = (datetime.now(pub.tzinfo) - pub).days
            return max(0.0, 1.0 - days / 365)
        except:
            return 0.5
    
    def _calc_keyword_score(self, item: Candidate, keywords: list[str]) -> float:
        """키워드 매칭 점수 계산 (0.0 ~ 1.0)"""
        if not keywords:
            return 0.5
        
        text = (item.title + " " + (item.abstract or "")).lower()
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return min(1.0, matches / max(len(keywords), 1))

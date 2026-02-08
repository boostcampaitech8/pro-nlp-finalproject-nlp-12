"""
Smart recommend service (ported from smart_recom).
Multi-source candidate merge + scoring.
"""
from __future__ import annotations

import asyncio
import json
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

import numpy as np
from sqlalchemy.orm import Session

from config import settings
from src.entity.paper import Paper
from src.repository.paper_repo import PaperRepository, PAPER_LIMIT
from src.repository.profile_repo import ProfileRepository
from src.repository.event_repo import EventRepository
from src.service.recsys.vector_utils import parse_vector_json
from src.service.recsys.user_vector import maybe_refresh_user_vector
from src.client.faiss_store import get_faiss_store
from src.client.arxiv_client import ArxivClient
from src.client.s2_client import S2Client
from src.schemas.summary import SummaryType

logger = logging.getLogger(__name__)

# 이벤트 가중치 (기존 smart 코드 유지)
EVENT_WEIGHTS = {
    "bookmark": 2.0,
    "like": 1.0,
    "click": 0.3,
    "impression": 0.0,
    "dislike": -2.0,
}

# 점수 계산 가중치
ALPHA = 0.45   # 벡터 유사도
GAMMA = 0.20   # 최신성
DELTA = 0.35   # 소스 신뢰도

SOURCE_WEIGHTS = {
    "faiss": 1.0,
    "arxiv": 0.6,
    "category": 0.2,
}


@dataclass
class Candidate:
    paper_id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: Optional[str]
    primary_category: Optional[str]
    categories: Optional[str]
    published_at: Optional[str]
    abs_url: Optional[str]
    pdf_url: Optional[str]
    source: str
    raw_score: float
    final_score: float = 0.0

class SmartRecommendService:
    """
    Smart 추천: FAISS + (arXiv placeholder) + category fallback
    """

    def __init__(
        self,
        db: Session,
        paper_service: Optional[Any] = None,
        valkey: Optional[Any] = None
    ):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.event_repo = EventRepository(db)
        self.faiss = get_faiss_store(
            dim=int(getattr(settings, "EMBED_DIM", 384)),
            index_path=getattr(settings, "FAISS_INDEX_PATH", "data/faiss/index.bin"),
        )
        self.paper_service = paper_service
        self.valkey = valkey
        self.arxiv_client = ArxivClient()
        self.s2_client = S2Client()

    def get_profile(self, user_id: str):
        return self.profile_repo.get(user_id)

    def _safe_json_list(self, val: Any) -> list[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(x) for x in val if x is not None]
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if x is not None]
            except Exception:
                pass
        return []

    def get_categories(self, user_id: str) -> list[str]:
        profile = self.get_profile(user_id)
        if not profile:
            return []
        # onboarding_json에서 survey/categories 키가 있을 수 있음
        data = getattr(profile, "onboarding_json", None)
        if isinstance(data, dict):
            for key in ("survey_categories", "categories", "category", "prefs"):
                cats = self._safe_json_list(data.get(key))
                if cats:
                    return cats
        return []

    def get_user_vector(self, user_id: str) -> Optional[np.ndarray]:
        profile = self.get_profile(user_id)
        if not profile:
            return None
        vec = parse_vector_json(getattr(profile, "user_vector_json", None))
        return vec if vec.size > 0 else None

    def get_seen_paper_ids(self, user_id: str) -> set[int]:
        # dislike만 제외 (smart 코드의 의도 유지)
        try:
            paper_ids = self.event_repo.get_interacted_paper_ids(
                user_id=user_id,
                event_types=["dislike"],
            )
            return set(int(x) for x in paper_ids)
        except Exception:
            return set()

    async def recommend(
        self,
        user_id: str,
        k: int = 30,
        use_faiss: bool = True,
        use_arxiv: bool = True,
        use_category: bool = True,
    ) -> dict:
        total_start = time.time()
        timings: dict[str, float] = {}

        maybe_refresh_user_vector(
            user_id=user_id,
            profile_repo=self.profile_repo,
            event_repo=self.event_repo,
            paper_repo=self.paper_repo,
        )

        # profile load
        t0 = time.time()
        categories = self.get_categories(user_id)
        user_vector = self.get_user_vector(user_id)
        timings["profile_load"] = round(time.time() - t0, 3)

        if user_vector is None:
            logger.warning(f"Cold start for user {user_id} - no preference vector")
            return {
                "items": [],
                "sources_used": [],
                "cold_start": True,
                "timings": timings,
            }

        candidates: list[Candidate] = []
        sources_used: list[str] = []

        t0 = time.time()
        seen_ids = self.get_seen_paper_ids(user_id)
        timings["seen_ids_load"] = round(time.time() - t0, 3)

        # [1] FAISS search
        if use_faiss:
            t0 = time.time()
            faiss_results = self._search_faiss(user_vector, n=100)
            timings["faiss_search"] = round(time.time() - t0, 3)
            candidates.extend(faiss_results)
            if faiss_results:
                sources_used.append("faiss")

        # [2] arXiv 실시간 검색 (DB 한도 미달 시에만)
        new_papers: list[dict] = []
        if use_arxiv and categories and self.paper_repo.count_all() < PAPER_LIMIT:
            t0 = time.time()
            arxiv_results, new_papers = await self._search_arxiv(
                categories=categories,
                exclude_ids=seen_ids,
                n=50,
            )
            timings["arxiv_search"] = round(time.time() - t0, 3)
            candidates.extend(arxiv_results)
            if arxiv_results:
                sources_used.append("arxiv")

        # [3] category fallback (recent)
        if use_category:
            t0 = time.time()
            cat_results = self._search_recent(exclude_ids=seen_ids, n=50)
            timings["category_search"] = round(time.time() - t0, 3)
            candidates.extend(cat_results)
            if cat_results:
                sources_used.append("category")

        # merge + score
        t0 = time.time()
        merged = self._merge_and_score(candidates, seen_ids)
        timings["merge_score"] = round(time.time() - t0, 3)

        items = []
        for c in merged[:k]:
            summary = await self.get_summary(c.arxiv_id, c.pdf_url)

            items.append({
                "paper_id": c.paper_id,
                "arxiv_id": c.arxiv_id,
                "title": c.title,
                "summary": summary,
                "primary_category": c.primary_category,
                "categories": c.categories,
                "published_date": c.published_at,
                "abs_url": c.abs_url,
                "pdf_url": c.pdf_url,
                "is_bookmarked": False,
                "is_liked": False,
            })

        timings["total"] = round(time.time() - total_start, 3)

        # 새로 추가된 논문의 S2 데이터를 백그라운드로 채움
        if new_papers:
            asyncio.create_task(self._enrich_s2_background(new_papers))

        return {
            "items": items,
            "sources_used": list(set(sources_used)),
            "cold_start": False,
            "timings": timings,
        }
    
    async def get_summary(self, arxiv_id: str, pdf_url: str):
        """
        캐시를 확인하여 논문 요약(Keypoint) 정보를 가져오거나, 없을 경우 새로 생성하여 캐싱합니다.
        """
        cache_key = f"summary:{arxiv_id}"
        cached_data = await self.valkey.get(cache_key)

        # 캐싱 데이터가 있는지 확인
        if cached_data:
            paper_data = json.loads(cached_data)
            summaries = paper_data.get("summaries")
        else:
            # 없으면 요약
            summaries = await self.paper_service.summarize_and_save(arxiv_id, pdf_url, is_store=True)
            # 새로 생성된 데이터는 valkey에 저장
            if summaries:
                summaries = {
                    s.summary_type.value: s.summary_text
                    for s in summaries
                }
                paper_data = {
                    "summaries": summaries,
                    "pdf_url": pdf_url
                }
                await self.valkey.setex(cache_key, 86400, json.dumps(paper_data))
            else:
                return None

        return summaries.get(SummaryType.keypoint.value)

    def _paper_meta(self, p: Paper) -> dict:
        arxiv_id = getattr(p, "arxiv_id", None) or ""
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
            "arxiv_id": arxiv_id,
            "abs_url": abs_url,
            "published_at": published_at,
            "primary_category": primary_category,
            "categories": categories,
        }

    def _search_faiss(self, user_vector: np.ndarray, n: int = 100) -> list[Candidate]:
        try:
            scores, ids = self.faiss.search(user_vector, k=n)
            if ids is None or len(ids) == 0:
                return []

            paper_ids = [int(pid) for pid in ids if int(pid) != -1]
            if not paper_ids:
                return []

            papers_list = self.paper_repo.get_by_ids(paper_ids)
            papers = {int(getattr(p, "id")): p for p in papers_list if getattr(p, "id", None) is not None}

            candidates: list[Candidate] = []
            for pid, sc in zip(ids, scores):
                if int(pid) == -1:
                    continue
                p = papers.get(int(pid))
                if not p:
                    continue

                raw = float(sc)
                normalized_score = min(1.0, max(0.5, 0.5 + (raw - 0.3) * 1.25))
                meta = self._paper_meta(p)

                candidates.append(
                    Candidate(
                        paper_id=int(p.id),
                        arxiv_id=meta["arxiv_id"],
                        title=getattr(p, "title", None) or "",
                        abstract=getattr(p, "abstract", None) or "",
                        authors=getattr(p, "authors", None),
                        primary_category=meta["primary_category"],
                        categories=meta["categories"],
                        published_at=meta["published_at"],
                        abs_url=meta["abs_url"],
                        pdf_url=getattr(p, "pdf_url", None),
                        source="faiss",
                        raw_score=normalized_score,
                    )
                )

            return candidates
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []

    def _search_recent(self, exclude_ids: set[int], n: int = 50) -> list[Candidate]:
        try:
            papers = self.paper_repo.get_recent_papers(limit=n + len(exclude_ids))
            candidates: list[Candidate] = []
            count = 0
            for p in papers:
                if int(p.id) in exclude_ids:
                    continue
                if count >= n:
                    break
                score = 0.5 - (count / max(n, 1)) * 0.2
                meta = self._paper_meta(p)
                candidates.append(
                    Candidate(
                        paper_id=int(p.id),
                        arxiv_id=meta["arxiv_id"],
                        title=getattr(p, "title", None) or "",
                        abstract=getattr(p, "abstract", None) or "",
                        authors=getattr(p, "authors", None),
                        primary_category=meta["primary_category"],
                        categories=meta["categories"],
                        published_at=meta["published_at"],
                        abs_url=meta["abs_url"],
                        pdf_url=getattr(p, "pdf_url", None),
                        source="category",
                        raw_score=score,
                    )
                )
                count += 1
            return candidates
        except Exception as e:
            logger.error(f"Recent papers search error: {e}")
            return []

    async def _search_arxiv(
        self,
        categories: list[str],
        exclude_ids: set[int],
        n: int = 50,
    ) -> tuple[list[Candidate], list[dict]]:
        """
        arXiv API 실시간 검색 → DB upsert → Candidate 리스트 반환.
        반환: (candidates, new_papers) — new_papers는 S2 enrichment 대상
        """
        try:
            raw_papers = await self.arxiv_client.search_combined(
                categories=categories or None,
                max_results=n,
            )
            if not raw_papers:
                return [], []

            candidates: list[Candidate] = []
            new_papers: list[dict] = []  # S2 enrichment 대상
            for data in raw_papers:
                # DB에 저장 (이미 있으면 기존 반환, 한도 초과 시 None)
                already_existed = self.paper_repo.get_paper_obj_by_arxiv_id(data["arxiv_id"])
                paper = self.paper_repo.upsert_from_arxiv(data)
                if paper is None:
                    continue

                # 새로 추가된 논문이면 S2 enrichment 대상
                if not already_existed:
                    new_papers.append({"paper_id": paper.id, "arxiv_id": paper.arxiv_id})

                if int(paper.id) in exclude_ids:
                    continue

                # FAISS에도 추가 (임베딩 생성 + 인덱싱)
                self._ensure_faiss_indexed(paper)

                meta = self._paper_meta(paper)
                candidates.append(
                    Candidate(
                        paper_id=int(paper.id),
                        arxiv_id=meta["arxiv_id"],
                        title=getattr(paper, "title", None) or "",
                        abstract=getattr(paper, "abstract", None) or "",
                        authors=None,
                        primary_category=meta["primary_category"],
                        categories=meta["categories"],
                        published_at=meta["published_at"],
                        abs_url=meta["abs_url"],
                        pdf_url=getattr(paper, "pdf_url", None),
                        source="arxiv",
                        raw_score=0.6,
                    )
                )

            logger.info(f"arXiv search returned {len(candidates)} candidates, {len(new_papers)} new")
            return candidates, new_papers
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return [], []

    async def _enrich_s2_background(self, new_papers: list[dict]):
        """
        백그라운드에서 새로 추가된 논문의 S2 메타데이터 + citation_edges를 채웁니다.
        recommend() 응답 이후 비동기로 실행됩니다.
        """
        for paper_info in new_papers:
            paper_id = paper_info["paper_id"]
            arxiv_id = paper_info["arxiv_id"]
            try:
                # 1) 인용 메타데이터 (citation_count, influential_citation_count, reference_count)
                metadata = await self.s2_client.get_paper_metadata(arxiv_id)
                if metadata:
                    self.paper_repo.update_s2_metadata(
                        paper_id=paper_id,
                        citation_count=metadata["citation_count"],
                        influential_citation_count=metadata["influential_citation_count"],
                        reference_count=metadata["reference_count"],
                    )

                # 2) 참조 논문 → citation_edges (DB에 있는 논문만 연결)
                references = await self.s2_client.get_references(arxiv_id)
                if references:
                    self.paper_repo.save_citation_edges(paper_id, references)

                logger.info(f"S2 enrichment done for paper {paper_id} ({arxiv_id})")
            except Exception as e:
                logger.warning(f"S2 enrichment failed for paper {paper_id}: {e}")

    def _ensure_faiss_indexed(self, paper: Paper):
        """논문이 FAISS 인덱스에 없으면 임베딩 생성 후 추가"""
        try:
            existing = self.faiss.get_existing_ids()
            if int(paper.id) in existing:
                return
            text = f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
            vec = self.faiss.embeddings.embed_documents([text])
            vec_np = np.array(vec, dtype="float32")
            self.faiss.add_with_ids([int(paper.id)], vec_np)
            self.faiss.persist()
        except Exception as e:
            logger.warning(f"FAISS indexing skipped for paper {paper.id}: {e}")

    def _merge_and_score(
        self,
        candidates: list[Candidate],
        seen_ids: set[int],
    ) -> list[Candidate]:
        # arxiv_id 기준 중복 제거
        seen_arxiv: dict[str, Candidate] = {}
        for c in candidates:
            if c.paper_id > 0 and c.paper_id in seen_ids:
                continue
            key = c.arxiv_id
            if key not in seen_arxiv or c.raw_score > seen_arxiv[key].raw_score:
                seen_arxiv[key] = c

        unique = list(seen_arxiv.values())

        for item in unique:
            recency = self._calc_recency(item.published_at)
            source_w = SOURCE_WEIGHTS.get(item.source, 0.5)

            item.final_score = (
                ALPHA * item.raw_score
                + GAMMA * recency
                + DELTA * source_w
            )

        unique.sort(key=lambda x: x.final_score, reverse=True)
        return unique

    def _calc_recency(self, published_at: Optional[str]) -> float:
        if not published_at:
            return 0.5
        try:
            if "T" in published_at:
                pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            else:
                pub = datetime.fromisoformat(published_at)
            days = (datetime.now(pub.tzinfo) - pub).days
            return max(0.0, 1.0 - days / 365)
        except Exception:
            return 0.5


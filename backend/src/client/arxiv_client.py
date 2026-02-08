"""
arXiv API 클라이언트

arXiv API를 사용하여 논문 정보를 실시간으로 가져옵니다.
"""
from __future__ import annotations

import asyncio
import logging
import feedparser
import urllib.parse
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# arXiv API rate limit: 최대 3 req/s, 여유 있게 0.4초 간격
_RATE_LIMIT_DELAY = 0.4


class ArxivClient:
    """arXiv API 클라이언트"""

    def __init__(self, base_url: str = "http://export.arxiv.org/api/query"):
        self.base_url = base_url
        self._last_call: float = 0.0

    async def _rate_limit(self):
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_call
        if elapsed < _RATE_LIMIT_DELAY:
            await asyncio.sleep(_RATE_LIMIT_DELAY - elapsed)
        self._last_call = asyncio.get_running_loop().time()

    async def search_by_category(
        self,
        category: str,
        max_results: int = 50,
        start: int = 0,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> list[dict]:
        """카테고리로 논문 검색 (예: cs.CL, cs.AI)"""
        query = f"cat:{category}"
        return await self._fetch(query, max_results, start, sort_by, sort_order)

    async def search_combined(
        self,
        categories: list[str] | None = None,
        max_results: int = 50,
    ) -> list[dict]:
        """여러 카테고리를 OR로 묶어 검색."""
        if not categories:
            return []

        cat_q = "+OR+".join(f"cat:{c}" for c in categories)
        query = f"({cat_q})"
        return await self._fetch(query, max_results, 0, "submittedDate", "descending")

    async def get_paper_by_id(self, arxiv_id: str) -> Optional[dict]:
        """arXiv ID로 특정 논문 1건 조회"""
        await self._rate_limit()
        url = f"{self.base_url}?id_list={arxiv_id}"
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)
        if feed.entries:
            return self._parse_entry(feed.entries[0])
        return None

    async def _fetch(
        self,
        query: str,
        max_results: int,
        start: int,
        sort_by: str,
        sort_order: str,
    ) -> list[dict]:
        await self._rate_limit()

        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

        logger.info(f"arXiv API call: {url}")
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        papers = []
        for entry in feed.entries:
            try:
                papers.append(self._parse_entry(entry))
            except Exception as e:
                logger.warning(f"arXiv entry parse error: {e}")
        return papers

    def _parse_entry(self, entry) -> dict:
        """feedparser entry → 논문 dict"""
        arxiv_id = entry.id.split("/abs/")[-1]

        # 카테고리
        categories = []
        primary_category = None
        if hasattr(entry, "tags"):
            categories = [tag.term for tag in entry.tags]
            if categories:
                primary_category = categories[0]

        # 날짜
        published_date = self._parse_date(getattr(entry, "published", None))
        updated_date = self._parse_date(getattr(entry, "updated", None))

        # PDF URL
        pdf_url = None
        if hasattr(entry, "links"):
            for link in entry.links:
                if link.get("type") == "application/pdf":
                    pdf_url = link.href
                    break

        return {
            "arxiv_id": arxiv_id,
            "title": entry.title.replace("\n", " ").strip() if hasattr(entry, "title") else "",
            "abstract": entry.summary.replace("\n", " ").strip() if hasattr(entry, "summary") else "",
            "primary_category": primary_category,
            "categories": categories,
            "published_date": published_date,
            "updated_date": updated_date,
            "pdf_url": pdf_url or f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        }

    @staticmethod
    def _parse_date(raw: Optional[str]):
        if not raw:
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").date()
        except Exception:
            return None

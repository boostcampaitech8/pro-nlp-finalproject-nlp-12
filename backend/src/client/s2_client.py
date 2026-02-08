"""
Semantic Scholar API 클라이언트

arXiv에서 가져온 논문의 인용 정보를 백그라운드로 채웁니다.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_RATE_LIMIT_DELAY = 0.35  # ~3 req/s (안전 마진)


class S2Client:
    """Semantic Scholar Graph API 클라이언트"""

    def __init__(self):
        self.api_key: str = settings.s2_api_key
        self._last_call: float = 0.0

    async def _rate_limit(self):
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_call
        if elapsed < _RATE_LIMIT_DELAY:
            await asyncio.sleep(_RATE_LIMIT_DELAY - elapsed)
        self._last_call = asyncio.get_running_loop().time()

    def _headers(self) -> dict:
        return {"x-api-key": self.api_key}

    async def get_paper_metadata(self, arxiv_id: str) -> Optional[dict]:
        """
        arxiv_id로 Semantic Scholar에서 인용 메타데이터를 가져옵니다.
        반환: {"citation_count": int, "influential_citation_count": int, "reference_count": int}
        """
        await self._rate_limit()
        url = (
            f"{S2_BASE_URL}/paper/ArXiv:{arxiv_id}"
            "?fields=citationCount,influentialCitationCount,referenceCount"
        )

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=self._headers())
                if resp.status_code == 404:
                    logger.info(f"S2: paper not found for ArXiv:{arxiv_id}")
                    return None
                resp.raise_for_status()
                data = resp.json()
                return {
                    "citation_count": data.get("citationCount"),
                    "influential_citation_count": data.get("influentialCitationCount"),
                    "reference_count": data.get("referenceCount"),
                }
        except Exception as e:
            logger.warning(f"S2 metadata fetch failed for {arxiv_id}: {e}")
            return None

    async def get_references(self, arxiv_id: str, limit: int = 500) -> list[dict]:
        """
        논문이 인용하는 참조 논문 목록을 가져옵니다.
        반환: [{"arxiv_id": str|None, "is_influential": bool}, ...]
        """
        await self._rate_limit()
        url = (
            f"{S2_BASE_URL}/paper/ArXiv:{arxiv_id}/references"
            f"?fields=isInfluential,externalIds&limit={limit}"
        )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=self._headers())
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("data", []):
                cited = item.get("citedPaper", {})
                external_ids = cited.get("externalIds") or {}
                ref_arxiv_id = external_ids.get("ArXiv")
                is_influential = item.get("isInfluential", False)
                results.append({
                    "arxiv_id": ref_arxiv_id,
                    "is_influential": is_influential,
                })
            return results
        except Exception as e:
            logger.warning(f"S2 references fetch failed for {arxiv_id}: {e}")
            return []

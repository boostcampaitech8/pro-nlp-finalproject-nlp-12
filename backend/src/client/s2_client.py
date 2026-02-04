"""
Semantic Scholar API 클라이언트

Semantic Scholar API를 사용하여 논문의 인용 정보, 영향력 등을 가져옵니다.
"""
import asyncio
import aiohttp
from typing import Dict, Optional, List
from src.utils.rate_limiter import RateLimiter


class SemanticScholarClient:
    """Semantic Scholar API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.semanticscholar.org/graph/v1"):
        self.base_url = base_url
        self.api_key = api_key
        # API key 유무에 따라 rate limit 조정
        # API key 있음: 10 calls/sec (안전하게), 없음: 1 call/sec
        max_calls = 10 if api_key else 1
        self.rate_limiter = RateLimiter(max_calls=max_calls, period=1.0)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager 진입"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def get_paper_by_arxiv_id(self, arxiv_id: str, fields: Optional[List[str]] = None) -> Optional[Dict]:
        """
        arXiv ID로 논문 정보 가져오기

        Args:
            arxiv_id: arXiv ID (예: 2301.12345)
            fields: 가져올 필드 리스트 (None이면 기본 필드 사용)

        Returns:
            논문 정보 또는 None
        """
        if fields is None:
            fields = [
                "paperId",
                "externalIds",
                "title",
                "abstract",
                "authors",
                "year",
                "citationCount",
                "influentialCitationCount",
                "referenceCount",
                "publicationDate",
                "citations",
                "references"
            ]

        await self.rate_limiter.acquire()

        url = f"{self.base_url}/paper/ARXIV:{arxiv_id}"
        params = {"fields": ",".join(fields)}

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(url, headers=self._get_headers(), params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    print(f"Error fetching paper {arxiv_id}: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"Exception fetching paper {arxiv_id}: {e}")
            return None

    async def get_paper_citations(self, paper_id: str, limit: int = 100) -> List[Dict]:
        """
        논문의 인용 정보 가져오기

        Args:
            paper_id: Semantic Scholar paper ID
            limit: 최대 결과 수

        Returns:
            인용 논문 리스트
        """
        await self.rate_limiter.acquire()

        url = f"{self.base_url}/paper/{paper_id}/citations"
        params = {
            "fields": "paperId,externalIds,title,year,citationCount",
            "limit": limit
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(url, headers=self._get_headers(), params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    print(f"Error fetching citations for {paper_id}: HTTP {response.status}")
                    return []
        except Exception as e:
            print(f"Exception fetching citations for {paper_id}: {e}")
            return []

    async def get_paper_references(self, paper_id: str, limit: int = 100) -> List[Dict]:
        """
        논문의 참고문헌 정보 가져오기

        Args:
            paper_id: Semantic Scholar paper ID
            limit: 최대 결과 수

        Returns:
            참고문헌 리스트
        """
        await self.rate_limiter.acquire()

        url = f"{self.base_url}/paper/{paper_id}/references"
        params = {
            "fields": "paperId,externalIds,title,year,citationCount",
            "limit": limit
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(url, headers=self._get_headers(), params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    print(f"Error fetching references for {paper_id}: HTTP {response.status}")
                    return []
        except Exception as e:
            print(f"Exception fetching references for {paper_id}: {e}")
            return []

    async def batch_get_papers(self, arxiv_ids: List[str]) -> List[Optional[Dict]]:
        """
        여러 논문 정보를 배치로 가져오기

        Args:
            arxiv_ids: arXiv ID 리스트

        Returns:
            논문 정보 리스트
        """
        tasks = [self.get_paper_by_arxiv_id(arxiv_id) for arxiv_id in arxiv_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(None)
            else:
                processed_results.append(result)

        return processed_results

    def parse_paper_data(self, s2_data: Dict, arxiv_data: Dict) -> Dict:
        """
        Semantic Scholar 데이터와 arXiv 데이터를 병합

        Args:
            s2_data: Semantic Scholar API 응답
            arxiv_data: arXiv API 응답

        Returns:
            병합된 논문 데이터
        """
        merged = {
            "arxiv_id": arxiv_data.get("arxiv_id"),
            "title": arxiv_data.get("title") or s2_data.get("title"),
            "abstract": arxiv_data.get("abstract") or s2_data.get("abstract"),
            "primary_category": arxiv_data.get("primary_category"),
            "categories": arxiv_data.get("categories", []),
            "published_date": arxiv_data.get("published_date"),
            "updated_date": arxiv_data.get("updated_date"),
            "abs_url": arxiv_data.get("abs_url"),
            "pdf_url": arxiv_data.get("pdf_url"),
            "citation_count": s2_data.get("citationCount") if s2_data else None,
            "influential_citation_count": s2_data.get("influentialCitationCount") if s2_data else None,
            "reference_count": s2_data.get("referenceCount") if s2_data else None,
        }

        return merged

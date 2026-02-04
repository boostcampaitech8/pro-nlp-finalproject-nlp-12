"""
arXiv API 클라이언트

arXiv API를 사용하여 논문 정보를 가져옵니다.
"""
import asyncio
import feedparser
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
from src.utils.rate_limiter import RateLimiter


class ArxivClient:
    """arXiv API 클라이언트"""

    def __init__(self, base_url: str = "http://export.arxiv.org/api/query"):
        self.base_url = base_url
        self.rate_limiter = RateLimiter(max_calls=3, period=1.0)  # 3 calls per second

    async def search_papers(
        self,
        category: str = "cs.CL",
        max_results: int = 100,
        start: int = 0,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> List[Dict]:
        """
        arXiv에서 논문 검색

        Args:
            category: 검색할 카테고리 (예: cs.CL, cs.AI, cs.LG)
            max_results: 최대 결과 수
            start: 시작 인덱스
            sort_by: 정렬 기준 (submittedDate, lastUpdatedDate, relevance)
            sort_order: 정렬 순서 (ascending, descending)

        Returns:
            논문 정보 리스트
        """
        await self.rate_limiter.acquire()

        # 검색 쿼리 구성
        query = f"cat:{category}"
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }

        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

        # feedparser는 동기 함수이므로 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        papers = []
        for entry in feed.entries:
            paper = self._parse_entry(entry)
            papers.append(paper)

        return papers

    async def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        arXiv ID로 특정 논문 가져오기

        Args:
            arxiv_id: arXiv ID (예: 2301.12345)

        Returns:
            논문 정보 또는 None
        """
        await self.rate_limiter.acquire()

        url = f"{self.base_url}?id_list={arxiv_id}"

        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        if feed.entries:
            return self._parse_entry(feed.entries[0])
        return None

    def _parse_entry(self, entry) -> Dict:
        """
        feedparser entry를 논문 정보 딕셔너리로 변환

        Args:
            entry: feedparser entry 객체

        Returns:
            논문 정보 딕셔너리
        """
        # arXiv ID 추출 (URL에서)
        arxiv_id = entry.id.split("/abs/")[-1]

        # abs URL (entry.id가 abs URL)
        abs_url = entry.id

        # 카테고리 추출
        categories = []
        primary_category = None
        if hasattr(entry, "tags"):
            categories = [tag.term for tag in entry.tags]
            if categories:
                primary_category = categories[0]

        # 날짜 파싱
        published_date = None
        if hasattr(entry, "published"):
            try:
                published_date = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ").date()
            except:
                published_date = None

        updated_date = None
        if hasattr(entry, "updated"):
            try:
                updated_date = datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%SZ").date()
            except:
                updated_date = None

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
            "abs_url": abs_url,
            "pdf_url": pdf_url or f"http://arxiv.org/pdf/{arxiv_id}.pdf",
        }

    async def search_by_date_range(
        self,
        category: str,
        start_date: str,
        end_date: str,
        max_results: int = 1000
    ) -> List[Dict]:
        """
        날짜 범위로 논문 검색

        Args:
            category: 카테고리
            start_date: 시작 날짜 (YYYYMMDD 형식)
            end_date: 종료 날짜 (YYYYMMDD 형식)
            max_results: 최대 결과 수

        Returns:
            논문 리스트
        """
        all_papers = []
        batch_size = 100  # arXiv API는 한 번에 최대 약 2000개까지 가능하지만 100개씩 나눠서 요청

        for start in range(0, max_results, batch_size):
            papers = await self.search_papers(
                category=category,
                max_results=min(batch_size, max_results - start),
                start=start,
                sort_by="submittedDate",
                sort_order="descending"
            )

            if not papers:
                break

            # 날짜 필터링
            filtered_papers = []
            for paper in papers:
                if paper.get("published_date"):
                    pub_date_str = paper["published_date"].strftime("%Y%m%d")
                    if start_date <= pub_date_str <= end_date:
                        filtered_papers.append(paper)

            all_papers.extend(filtered_papers)

            # 날짜 범위를 벗어나면 중단
            if papers and papers[-1].get("published_date"):
                last_date_str = papers[-1]["published_date"].strftime("%Y%m%d")
                if last_date_str < start_date:
                    break

            # 짧은 대기
            await asyncio.sleep(1)

        return all_papers

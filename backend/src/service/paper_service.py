from src.repository.paper_repo import PaperRepository
from src.repository.summary_repo import SummaryRepository
from src.repository.event_repo import EventRepository
from src.service.summarization.parse_service import ParseService
from src.service.summarization.summarize_service import SummarizeService
from src.client.clova_client import ClovaClient
from src.schemas.search import SearchResponse
from src.schemas.summary import SummaryResponse, SummaryDetail, SummaryType
from src.entity.user_event import EventType
from langchain_core.documents import Document
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import json

class PaperService:
    def __init__(
        self,
        db: Session,
        search_service: Optional[Any] = None,
        valkey: Optional[Any] = None
    ):
        self.db = db
        self.clova_client = ClovaClient()
        self.search_service = search_service
        self.parse_service = ParseService()
        self.summarize_service = SummarizeService(self.clova_client)
        self.paper_repository = PaperRepository(self.db)
        self.event_repository = EventRepository(self.db)
        self.summary_repository = SummaryRepository(self.db)
        self.valkey = valkey

    async def summarize_and_save(self, arxiv_id: str, pdf_url: str, is_store: bool = True) -> List[SummaryDetail]:
        """
        논문을 번역 및 요약한 후 선택적으로 DB에 저장합니다.
        """
        # pdf 파싱 및 요약, 번역
        pdf_text = await self.parse_service.get_text_by_url(pdf_url)
        response = await self.summarize_service.summarize(pdf_text)

        # 요약을 실패한 경우 빈 리스트 반환
        if not isinstance(response, dict):
            return []
        
        # 논문 요약 내용 저장
        summary_infos = []
        for summary_type, summary_text in response.items():
            summary_infos.append({
                "summary_type": summary_type,
                "summary_text": summary_text
            })

        # DB 저장
        if is_store:
            paper_id = self.paper_repository.get_paper_by_arxiv_id(arxiv_id)
            self.summary_repository.save(paper_id, summary_infos)
        
        return [SummaryDetail(**info) for info in summary_infos]

    async def hybrid_search(self, user_id: str, query: str = "Attention mechanism의 효율성과 연산량 최적화 방법") -> List[SearchResponse]:
        """
        하이브리드 검색을 수행합니다.
        """
        docs = await self.search_service.search(query)

        search_results = []
        for doc in docs:
            paper_id = paper_id=doc.metadata.get("paper_id")

            # 좋아요, 북마크 여부
            is_liked = self.event_repository.exists_event(
                user_id=user_id,
                paper_id=paper_id,
                event_type=EventType.like.value
            )
            is_bookmarked = self.event_repository.exists_event(
                user_id=user_id,
                paper_id=paper_id,
                event_type=EventType.bookmark.value
            )

            pdf_url = doc.metadata.get("pdf_url")
            abs_url = pdf_url.replace("pdf", "abs").removesuffix(".abs")

            search_results.append(
                SearchResponse(
                    paper_id=paper_id,
                    arxiv_id=doc.metadata.get("arxiv_id"),
                    title=doc.metadata.get("title"),
                    pdf_url=pdf_url,
                    abs_url=abs_url,
                    published_date=doc.metadata.get("published_date"),
                    summary=doc.metadata.get("summary"),
                    is_liked=is_liked,
                    is_bookmarked=is_bookmarked,
                    primary_category=doc.metadata.get("primary_category"),
                    categories=doc.metadata.get("categories")
                )
            )

        return search_results
    
    # [수정] paper_id: int + arxiv_id: str (스마트 모드 고려)
    async def get_summaries_and_log_click(
        self,
        user_id: str,
        paper_id: Optional[int] = None,
        arxiv_id: Optional[str] = None
    ) -> SummaryResponse:
        """
        paper_id 또는 arxiv_id 중 하나를 받아
        keypoint를 제외한 요약을 반환합니다.

        paper_id를 입력받은 경우 클릭 로그를 남깁니다.
        """
        if paper_id:
            # 클릭 로그 저장
            self.event_repository.create(
                user_id=user_id,
                paper_id=paper_id,
                event_type=EventType.click.value
            )

            # paper entity 확보
            paper = self.paper_repository.get_by_id(paper_id)
            arxiv_id = paper.arxiv_id

        # 캐싱 데이터 확인
        cache_key = f"summary:{arxiv_id}"
        cached_data = await self.valkey.get(cache_key)
        pdf_url = None
        summaries = None

        if cached_data:
            paper_data = json.loads(cached_data)
            summaries = paper_data.get("summaries")
            pdf_url = paper_data.get("pdf_url")
        elif paper_id:
            # 논문 요약 조회 및 반환
            summaries = self.summary_repository.get_summaries(paper_id)
            summaries = {
                s.summary_type.value: s.summary_text
                for s in summaries
            }
            pdf_url=paper.pdf_url
            paper_data = {
                "summaries": summaries,
                "pdf_url": pdf_url
            }

            # 캐싱
            await self.valkey.setex(cache_key, 86400, json.dumps(paper_data))
            
        pdf_url = str(pdf_url) if pdf_url else None
        abs_url = pdf_url.replace("pdf", "abs").removesuffix(".abs") if pdf_url else None
        
        if not summaries:
            summaries = {}

        summary_details = []
        for summary_type, summary_text in summaries.items():
            if summary_type != SummaryType.keypoint.value:
                summary_details.append(SummaryDetail(
                    summary_type=summary_type,
                    summary_text=summary_text
                ))

        return SummaryResponse(
            paper_id=paper_id,
            pdf_url=pdf_url,
            abs_url=abs_url,
            summaries=summary_details
        )
from src.repository.paper_repo import PaperRepository
from src.repository.summary_repo import SummaryRepository
from src.repository.event_repo import EventRepository
from src.service.search.search_service import SearchService
from src.service.summarization.parse_service import ParseService
from src.service.summarization.summarize_service import SummarizeService
from src.client.clova_client import ClovaClient
from src.schemas.search import SearchResponse
from src.schemas.summary import SummaryResponse
from src.entity.user_event import EventType
from langchain_core.documents import Document
from sqlalchemy.orm import Session
from typing import List

class PaperService:
    def __init__(self, db: Session, faiss_service, all_docs: list[Document]):
        self.db = db
        self.clova_client = ClovaClient()
        self.search_service = SearchService(faiss_service, all_docs)
        self.parse_service = ParseService()
        self.summarize_service = SummarizeService(self.clova_client)
        self.paper_repository = PaperRepository(self.db)
        self.event_repository = EventRepository(self.db)
        self.summary_repository = SummaryRepository(self.db)

    async def summarize_and_save(self, arxiv_id: str, pdf_url: str):
        """
        논문을 번역 및 요약한 후 DB에 저장합니다.
        """
        # pdf 파싱 및 요약, 번역
        pdf_text = await self.parse_service.get_text_by_url(pdf_url)
        response = await self.summarize_service.summarize(pdf_text)

        # 논문 요약 내용 저장
        summary_infos = []
        for summary_type, summary_text in response.items():
            summary_infos.append({
                "summary_type": summary_type,
                "summary_text": summary_text
            })

        paper_id = self.paper_repository.get_id_by_arxiv_id(arxiv_id)

        self.summary_repository.save(paper_id, summary_infos)

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
                    is_bookmarked=is_bookmarked
                )
            )

        return search_results
    
    def get_summaries_and_log_click(self, user_id: str, paper_id: int) -> List[SummaryResponse]:
        """
        클릭 이벤트를 저장하고, keypoint를 제외한 요약을 반환합니다.
        """
        # 클릭 로그 저장
        self.event_repository.create(
            user_id=user_id,
            paper_id=paper_id,
            event_type=EventType.click.value
        )

        # 논문 요약 조회 및 반환
        results = self.summary_repository.get_summaries_except_keypoint(paper_id)

        return [
            SummaryResponse(
                paper_id=r.paper_id,
                summary_type=r.summary_type,
                summary_text=r.summary_text
            ) for r in results
        ]
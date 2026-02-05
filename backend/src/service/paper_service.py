from src.repository.paper_repository import PaperRepository
from src.repository.summary_repository import SummaryRepository
from src.repository.user_event_repository import UserEventRepository
from src.service.search.search_service import SearchService
from src.service.summarization.parse_service import ParseService
from src.service.summarization.summarize_service import SummarizeService
from src.client.clova_client import ClovaClient
from src.schemas.search_schema import SearchResponse
from src.schemas.summary_schema import SummaryResponse
from langchain_core.documents import Document
from typing import List

class PaperService:
    def __init__(self, faiss_service, all_docs: list[Document]):
        self.clova_client = ClovaClient()
        self.search_service = SearchService(faiss_service, all_docs)
        self.parse_service = ParseService()
        self.summarize_service = SummarizeService(self.clova_client)

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

        paper_id = PaperRepository.get_id_by_arxiv_id(arxiv_id)

        SummaryRepository.save(paper_id, summary_infos)

    async def hybrid_search(self, query: str = "Attention mechanism의 효율성과 연산량 최적화 방법") -> List[SearchResponse]:
        """
        하이브리드 검색을 수행합니다.
        """
        results = await self.search_service.search(query)
        return [
            SearchResponse(
                paper_id=doc.metadata.get("paper_id"),
                arxiv_id=doc.metadata.get("arxiv_id"),
                title=doc.metadata.get("title"),
                pdf_url=doc.metadata.get("pdf_url"),
                published_date=doc.metadata.get("published_date"),
                summary=doc.metadata.get("summary")
            )
            for doc in results
        ]
    
    def get_summaries_and_log_click(self, user_id: int, paper_id: int) -> List[SummaryResponse]:
        """
        클릭 이벤트를 저장하고, keypoint를 제외한 요약을 반환합니다.
        """
        # 클릭 로그 저장
        UserEventRepository.save_click(user_id, paper_id)

        # 논문 요약 조회 및 반환
        results = SummaryRepository.get_summaries_except_keypoint(paper_id)

        return [
            SummaryResponse(
                paper_id=r.paper_id,
                summary_type=r.summary_type,
                summary_text=r.summary_text
            ) for r in results
        ]
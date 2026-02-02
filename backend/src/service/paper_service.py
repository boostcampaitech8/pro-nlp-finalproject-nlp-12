from src.repository.paper_repository import PaperRepository
from src.repository.summary_repository import SummaryRepository
from src.service.paper.search_service import SearchService
from src.service.paper.parse_service import ParseService
from src.service.paper.summarize_service import SummarizeService
from src.client.gpt_client import GPTClient

class PaperService:
    def __init__(self, vectorstore, all_papers):
        self.gpt_client = GPTClient()
        self.search_service = SearchService(vectorstore, all_papers)
        self.parse_service = ParseService()
        self.summarize_service = SummarizeService(self.gpt_client)

    async def summarize_and_save(self, arxiv_id: str):
        """
        논문을 번역 및 요약한 후 DB에 저장합니다.
        """
        # pdf 파싱 및 요약, 번역
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
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

    async def hybrid_search(self, query: str = "Attention mechanism의 효율성과 연산량 최적화 방법"):
        """
        하이브리드 검색을 수행합니다.
        """
        results = await self.search_service.search(query)
        return [
            {
                "arxiv_id": doc.metadata.get("arxiv_id"),
                "title": doc.metadata.get("title"),
                "abstract": doc.metadata.get("abstract"),
                "pdf_url": doc.metadata.get("pdf_url"),
                "score": doc.metadata.get("rrf_score"),

                "sparse_rank": doc.metadata.get("sparse_rank"),
                "dense_rank": doc.metadata.get("dense_rank"),
                "final_rank": doc.metadata.get("final_rank"),
            }
            for doc in results
        ]
from src.repository.paper_repository import PaperRepository
from src.service.paper.search_service import SearchService
from src.service.paper.parse_service import ParseService
from src.service.paper.summarize_service import SummarizeService
from src.client.gpt_client import GPTClient
from src.service.vector_service import VectorService

gpt_client = GPTClient()

all_papers = PaperRepository.get_papers_as_documents()

vector_service = VectorService()
vectorstore = vector_service.initialize_index(all_papers)

search_service = SearchService(vectorstore, all_papers)
parse_service = ParseService()
summarize_service = SummarizeService(gpt_client)

class PaperService:
    @staticmethod
    async def summarize(arxiv_id: str):
        """
        논문을 요약합니다.
        """
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_text = await parse_service.get_text_by_url(pdf_url)
        response = await summarize_service.summarize(pdf_text)
        return response
        
    @staticmethod
    async def hybrid_search(query: str = "Attention mechanism의 효율성과 연산량 최적화 방법"):
        """
        하이브리드 검색을 수행합니다.
        """
        results = await search_service.search(query)
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
from src.database.mysql import get_mysql_db
from src.entity.paper import Paper
from src.entity.summary import Summary, SummaryType
from langchain_core.documents import Document

class PaperRepository:
    @staticmethod
    def get_paper_by_arxiv_id(arxiv_id: str) -> int:
        """
        arxiv_id를 기반으로 DB에서 paper_id를 조회합니다.
        """
        with get_mysql_db() as db:
            paper = db.query(Paper).filter(Paper.arxiv_id==arxiv_id).first()
            return paper.id
        
    @staticmethod
    def get_papers_as_documents() -> list[Document]:
        """
        DB에서 모든 논문 데이터 조회
        """
        with get_mysql_db() as db:
            results = db.query(Paper, Summary.summary_text).join(
                Summary, Paper.id==Summary.paper_id
            ).filter(
                Summary.summary_type==SummaryType.keypoint
            ).all()

            docs = []
            for p, keypoint_text in results:
                # 제목과 초록을 묶어 질의와의 유사도를 비교하는 데에 사용
                content = f"Title: {p.title}\n\nAbstract: {p.abstract}"

                metadata = {
                    "paper_id": p.id,
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "abstract": p.abstract,
                    "pdf_url": str(p.pdf_url) if p.pdf_url else None,
                    "published_date": p.published_date.isoformat() if p.published_date else None,
                    "summary": keypoint_text
                }

                docs.append(Document(page_content=content, metadata=metadata))
            
            return docs
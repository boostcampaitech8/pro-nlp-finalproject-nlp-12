from src.database.mysql import get_mysql_db
from src.entity.paper import Paper
from langchain_core.documents import Document

class PaperRepository:
    @staticmethod
    def get_papers_as_documents() -> list[Document]:
        """
        DB에서 모든 논문 데이터 조회
        """
        with get_mysql_db() as db:
            papers = db.query(Paper).all()

            docs = []
            for paper in papers:
                # 제목과 초록을 묶어 질의와의 유사도를 비교하는 데에 사용
                content = f"Title: {paper.title}\n\nAbstract: {paper.abstract}"

                metadata = {
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "pdf_url": paper.pdf_url
                }

                docs.append(Document(page_content=content, metadata=metadata))
            
            return docs

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from src.entity.paper import Paper
from src.entity.summary import Summary, SummaryType
from src.entity.primary_category import PrimaryCategory
from src.entity.paper_category import PaperCategory
from langchain_core.documents import Document

class PaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, paper_id: int) -> Paper | None:
        stmt = select(Paper).where(Paper.id == paper_id)
        return self.db.execute(stmt).scalars().first()

    def get_by_ids(self, ids: list[int]) -> list[Paper]:
        if not ids:
            return []
        stmt = select(Paper).where(Paper.id.in_(ids))
        return self.db.execute(stmt).scalars().all()

    def fetch_batch(self, offset: int, limit: int) -> list[Paper]:
        stmt = select(Paper).order_by(Paper.id).offset(offset).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def get_recent_papers(self, limit: int = 100) -> list[Paper]:
        if hasattr(Paper, "published_date"):
            stmt = select(Paper).order_by(desc(getattr(Paper, "published_date"))).limit(limit)
        else:
            stmt = select(Paper).order_by(desc(getattr(Paper, "id"))).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def count_all(self) -> int:
        return self.db.query(Paper).count()
    
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> int:
        """
        arxiv_id를 기반으로 DB에서 paper_id를 조회합니다.
        """
        paper = self.db.query(Paper).filter(Paper.arxiv_id==arxiv_id).first()
        return paper.id
        
    def get_papers_as_documents(self) -> list[Document]:
        """
        DB에서 모든 논문 데이터 조회
        """
        results = self.db.query(Paper, Summary.summary_text).join(
            Summary, Paper.id==Summary.paper_id
        ).options(
            joinedload(Paper.primary_category).joinedload(PrimaryCategory.category),
            joinedload(Paper.paper_categories).joinedload(PaperCategory.category)
        ).filter(
            Summary.summary_type==SummaryType.keypoint
        ).all()

        docs = []
        for p, keypoint_text in results:
            # 제목과 초록을 묶어 질의와의 유사도를 비교하는 데에 사용
            content = f"Title: {p.title}\n\nAbstract: {p.abstract}"

            primary_category = None
            if p.primary_category and p.primary_category.category:
                primary_category = p.primary_category.category.category_type

            category_list = []
            if p.paper_categories:
                for pc in p.paper_categories:
                    if pc.category:
                        category_list.append(pc.category.category_type)
            
            categories = ", ".join(category_list) if category_list else None

            metadata = {
                "paper_id": p.id,
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "abstract": p.abstract,
                "pdf_url": str(p.pdf_url) if p.pdf_url else None,
                "published_date": p.published_date.isoformat() if p.published_date else None,
                "summary": keypoint_text,
                "primary_category": primary_category,
                "categories": categories
            }

            docs.append(Document(page_content=content, metadata=metadata))
            
        return docs

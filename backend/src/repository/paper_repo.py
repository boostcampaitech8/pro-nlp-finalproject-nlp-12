from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from src.entity.paper import Paper
from src.entity.summary import Summary, SummaryType
from src.entity.primary_category import PrimaryCategory
from src.entity.category import Category
from src.entity.paper_category import PaperCategory
from src.entity.citation_edge import CitationEdge
from langchain_core.documents import Document

PAPER_LIMIT = 12800

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

    def get_recent_papers_by_primary_category(self, category_type: str, limit: int = 50) -> list[Paper]:
        stmt = (
            select(Paper)
            .join(PrimaryCategory, Paper.id == PrimaryCategory.paper_id)
            .join(Category, Category.id == PrimaryCategory.category_id)
            .where(Category.category_type == category_type)
        )
        if hasattr(Paper, "published_date"):
            stmt = stmt.order_by(desc(getattr(Paper, "published_date")))
        else:
            stmt = stmt.order_by(desc(getattr(Paper, "id")))
        return self.db.execute(stmt.limit(limit)).scalars().all()

    def get_recent_papers_by_any_category(self, category_type: str, limit: int = 50) -> list[Paper]:
        stmt = (
            select(Paper)
            .join(PaperCategory, Paper.id == PaperCategory.paper_id)
            .join(Category, Category.id == PaperCategory.category_id)
            .where(Category.category_type == category_type)
        )
        if hasattr(Paper, "published_date"):
            stmt = stmt.order_by(desc(getattr(Paper, "published_date")))
        else:
            stmt = stmt.order_by(desc(getattr(Paper, "id")))
        return self.db.execute(stmt.limit(limit)).scalars().all()

    def count_all(self) -> int:
        return self.db.query(Paper).count()
    
    def get_id_by_arxiv_id(self, arxiv_id: str) -> int | None:
        """
        arxiv_id를 기반으로 DB에서 paper_id를 조회합니다.
        """
        paper = self.db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
        return paper.id if paper else None

    def get_paper_obj_by_arxiv_id(self, arxiv_id: str) -> Paper | None:
        stmt = select(Paper).where(Paper.arxiv_id == arxiv_id)
        return self.db.execute(stmt).scalars().first()

    def upsert_from_arxiv(self, data: dict) -> Paper:
        """
        arXiv API 응답 dict → Paper 생성 또는 기존 반환.
        카테고리(PrimaryCategory, PaperCategory)도 함께 저장.
        """
        existing = self.get_paper_obj_by_arxiv_id(data["arxiv_id"])
        if existing:
            return existing

        if self.count_all() >= PAPER_LIMIT:
            return None

        paper = Paper(
            arxiv_id=data["arxiv_id"],
            title=data.get("title", ""),
            abstract=data.get("abstract", ""),
            pdf_url=data.get("pdf_url"),
            published_date=data.get("published_date"),
            updated_date=data.get("updated_date"),
        )
        self.db.add(paper)
        self.db.flush()  # paper.id 확보

        # 카테고리 저장
        primary_cat_type = data.get("primary_category")
        cat_types = data.get("categories") or []

        if primary_cat_type:
            cat_obj = self._get_or_create_category(primary_cat_type)
            pc = PrimaryCategory(paper_id=paper.id, category_id=cat_obj.id)
            self.db.add(pc)

        for ct in cat_types:
            cat_obj = self._get_or_create_category(ct)
            exists = self.db.query(PaperCategory).filter_by(
                paper_id=paper.id, category_id=cat_obj.id
            ).first()
            if not exists:
                self.db.add(PaperCategory(paper_id=paper.id, category_id=cat_obj.id))

        self.db.commit()
        self.db.refresh(paper)
        return paper

    def update_s2_metadata(
        self,
        paper_id: int,
        citation_count: int | None,
        influential_citation_count: int | None,
        reference_count: int | None,
    ):
        """S2에서 가져온 인용 메타데이터를 업데이트합니다."""
        paper = self.get_by_id(paper_id)
        if not paper:
            return
        paper.citation_count = citation_count
        paper.influential_citation_count = influential_citation_count
        paper.reference_count = reference_count
        self.db.commit()

    def save_citation_edges(self, seed_id: int, references: list[dict]):
        """
        S2 references 데이터를 citation_edges에 저장합니다.
        references: [{"arxiv_id": str|None, "is_influential": bool}, ...]
        DB에 존재하는 논문만 연결합니다.
        """
        for ref in references:
            ref_arxiv_id = ref.get("arxiv_id")
            if not ref_arxiv_id:
                continue
            cited_paper = self.get_paper_obj_by_arxiv_id(ref_arxiv_id)
            if not cited_paper:
                continue
            # 중복 체크
            exists = self.db.query(CitationEdge).filter_by(
                seed_id=seed_id, cited_paper_id=cited_paper.id
            ).first()
            if not exists:
                self.db.add(CitationEdge(
                    seed_id=seed_id,
                    cited_paper_id=cited_paper.id,
                    is_influential=ref.get("is_influential", False),
                ))
        self.db.commit()

    def _get_or_create_category(self, category_type: str) -> Category:
        cat = self.db.query(Category).filter(Category.category_type == category_type).first()
        if cat:
            return cat
        cat = Category(category_type=category_type)
        self.db.add(cat)
        self.db.flush()
        return cat
        
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

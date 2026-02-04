"""논문 상세 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.repository.paper_repository import PaperRepository

router = APIRouter(prefix="/api/paper", tags=["paper"])


### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정
class PaperDetailResponse(BaseModel):
    """논문 상세 응답"""
    paper_id: int
    arxiv_id: str | None = None
    title: str
    abstract: str | None = None
    published_date: str | None = None
    pdf_url: str | None = None
    citation_count: int = 0


@router.get("/{paper_id}", response_model=PaperDetailResponse)
def get_paper_detail(paper_id: int, db: Session = Depends(get_db)):
    """논문 상세 정보 조회"""
    repo = PaperRepository(db)
    paper = repo.get_by_id(paper_id)

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return PaperDetailResponse(
        paper_id=paper.id,
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        abstract=paper.abstract,
        published_date=paper.published_date.isoformat() if paper.published_date else None,
        pdf_url=paper.pdf_url,
        citation_count=paper.citation_count or 0,
    )

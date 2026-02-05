# src/api/paper.py  (네 구조에 맞게 파일 위치는 동일하게)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session
from src.database.mysql import get_db
from src.repository.paper_repo import PaperRepository

router = APIRouter(prefix="/paper", tags=["paper"])


class PaperDetailOut(BaseModel):
    paper_id: int
    title: str
    abstract: str | None = None
    web_url: str | None = None
    pdf_url: str | None = None


@router.get("/{paper_id}", response_model=PaperDetailOut)
def get_paper_detail(paper_id: int, db: Session = Depends(get_db)):
    repo = PaperRepository(db)
    paper = repo.get_by_id(paper_id)

    if not paper:
        raise HTTPException(status_code=404, detail="paper not found")

    # ✅ Paper 엔티티 필드명이 프로젝트마다 달라서 getattr로 안전하게 처리
    arxiv_id = getattr(paper, "arxiv_id", None)
    web_url = getattr(paper, "web_url", None) or getattr(paper, "url", None)
    if web_url is None and arxiv_id:
        web_url = f"https://arxiv.org/abs/{arxiv_id}"

    return PaperDetailOut(
        paper_id=paper.id,
        title=getattr(paper, "title", ""),
        abstract=getattr(paper, "abstract", None),
        web_url=web_url,
        pdf_url=getattr(paper, "pdf_url", None),
    )

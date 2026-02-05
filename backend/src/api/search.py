from fastapi import APIRouter, Depends, Request
from src.service.paper_service import PaperService
from src.schemas.search import SearchRequest, SearchResponse
from sqlalchemy.orm import Session
from src.database.mysql import get_mysql_db
from typing import List

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

# 서비스 인스턴스를 관리하는 함수(의존성 주입용)
def get_paper_service(
    request: Request,
    db: Session = Depends(get_mysql_db)
) -> PaperService:
    faiss_store = request.app.state.faiss_store
    all_papers = request.app.state.all_papers
    return PaperService(db, faiss_store, all_papers)

@router.post("/", response_model=List[SearchResponse])
async def get_papers(
    request: SearchRequest,
    service: PaperService = Depends(get_paper_service)    
):
    """
    논문 검색 결과를 반환합니다.
    """
    return await service.hybrid_search(request.user_id, request.query)
from fastapi import APIRouter, Depends, Request
from src.service.paper_service import PaperService
from src.schemas.summary import SummaryRequest, SummaryResponse
from sqlalchemy.orm import Session
from src.database.mysql import get_mysql_db
from typing import List

router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

# 서비스 인스턴스를 관리하는 함수(의존성 주입용)
def get_paper_service(
    request: Request,
    db: Session = Depends(get_mysql_db)
) -> PaperService:
    faiss_store = request.app.state.faiss_store
    all_papers = request.app.state.all_papers
    return PaperService(db, faiss_store, all_papers)

@router.post("/", response_model=SummaryResponse)
async def read_summaries(
    request: SummaryRequest,
    service: PaperService = Depends(get_paper_service)    
):
    """
    클릭 이벤트를 저장하고 논문 요약본을 반환합니다.
    """
    return service.get_summaries_and_log_click(request.user_id, request.paper_id)
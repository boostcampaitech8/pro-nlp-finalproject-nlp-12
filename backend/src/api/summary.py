from fastapi import APIRouter, Depends, Request
from src.service.paper_service import PaperService
from src.schemas.search_schema import SearchResponse
from src.schemas.summary_schema import SummaryRequest, SummaryResponse
from typing import List

router = APIRouter(
    prefix="/api/summary",
    tags=["Summary"]
)

# 서비스 인스턴스를 관리하는 함수(의존성 주입용)
def get_paper_service(request: Request) -> PaperService:
    return request.app.state.paper_service

@router.post("/", response_model=List[SummaryResponse])
async def read_summaries(
    request: SummaryRequest,
    service: PaperService = Depends(get_paper_service)    
):
    """
    논문 검색 결과를 반환합니다.
    """
    return service.get_summaries_and_log_click(request.user_id, request.paper_id)
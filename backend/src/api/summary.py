from src.schemas.summary import SummaryRequest, SummaryResponse
from fastapi import APIRouter, Depends
from src.service.paper_service import PaperService
from src.api.dependencies import get_paper_service

router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/", response_model=SummaryResponse)
async def read_summaries(
    request: SummaryRequest,
    service: PaperService = Depends(get_paper_service)    
):
    """
    클릭 이벤트를 저장하고 논문 요약본을 반환합니다.
    """
    return await service.get_summaries_and_log_click(request.user_id, request.paper_id, request.arxiv_id)
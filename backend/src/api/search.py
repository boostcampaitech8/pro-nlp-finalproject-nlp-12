from fastapi import APIRouter, Depends
from src.service.paper_service import PaperService
from src.schemas.search import SearchRequest, SearchResponse
from src.api.dependencies import get_paper_service
from typing import List

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

@router.post("/", response_model=List[SearchResponse])
async def get_papers(
    request: SearchRequest,
    service: PaperService = Depends(get_paper_service)    
):
    """
    논문 검색 결과를 반환합니다.
    """
    return await service.hybrid_search(request.user_id, request.query)
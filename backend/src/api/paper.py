from fastapi import APIRouter
from typing import List

from src.service.paper_service import LikeService
from src.schemas.paper import LikeRequest, LikeResponse, PaperResponse

router = APIRouter(
    prefix="/api/paper",
    tags=["Paper"]
)

@router.post("/like", response_model=LikeResponse)
def toggle_paper_like(request: LikeRequest):
    """
    사용자의 '좋아요' 상태를 토글하고 최종 상태를 반환합니다.
    """
    new_state = LikeService.toggle(
        session_id=request.session_id,
        arxiv_id=request.arxiv_id
    )

    return {"is_liked": new_state}

@router.get("/like", response_model=PaperResponse)
async def get_liked_papers(session_id: str):
    """
    사용자가 좋아요를 누른 논문을 제공합니다.
    """
    return LikeService.get_liked_papers(session_id)
from src.repository.like_repository import LikeRepository
from src.repository.paper_repository import PaperRepository
from src.schemas.paper import PaperResponse
from typing import List, Dict

class LikeService:
    @staticmethod
    def toggle(session_id: str, arxiv_id: str) -> bool:
        """
        '좋아요' 상태를 토글합니다.
        """
        return LikeRepository.toggle(session_id, arxiv_id)
    
    @staticmethod
    def get_liked_papers(session_id: str) -> List[PaperResponse]:
        """
        사용자가 '좋아요'한 논문을 모두 반환합니다.
        """
        paper_res = PaperRepository.get_liked_papers_by_session_id(session_id)
        return [PaperResponse(**p) for p in paper_res]
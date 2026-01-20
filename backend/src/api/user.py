from fastapi import APIRouter
from src.service.user_service import UserService
from src.schemas.user import SessionResponse

router = APIRouter(
    prefix="/api/user",
    tags=["User"]
)

@router.get("", response_model=SessionResponse)
def create_session_id():
    """
    생성한 session_id를 제공합니다.
    """
    new_session_id = UserService.get_session_id()
    return {"session_id": new_session_id}
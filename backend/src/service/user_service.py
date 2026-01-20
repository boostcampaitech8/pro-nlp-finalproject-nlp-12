from uuid import uuid4
from src.repository.user_repository import UserRepository

class UserService:
    @staticmethod
    def get_session_id() -> str:
        """
        생성한 session_id를 DB에 저장한 뒤 반환합니다.
        """
        new_session_id = str(uuid4())
        UserRepository.save(new_session_id)
        return new_session_id
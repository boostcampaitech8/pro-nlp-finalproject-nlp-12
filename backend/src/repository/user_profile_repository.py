"""User Profile Repository - 사용자 프로필 데이터 접근 계층"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from src.entity.user import User
from src.repository.base import BaseRepository


class UserProfileRepository(BaseRepository[User]):
    """사용자 프로필 Repository"""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_user_id(self, user_id: str) -> Optional[User]:
        """사용자 ID(uuid)로 프로필 조회"""
        stmt = select(User).where(User.uuid == user_id)
        return self.db.execute(stmt).scalars().first()
    
    def get_latest_by_user_id(self, user_id: str) -> Optional[User]:
        """사용자의 최신 프로필 조회 (updated_at 기준)"""
        stmt = (
            select(User)
            .where(User.uuid == user_id)
            .order_by(desc(User.updated_at))
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()
    
    def create_or_update(self, user_id: str, profile_data: dict) -> User:
        """프로필 생성 또는 업데이트"""
        existing = self.get_by_user_id(user_id)
        
        if existing:
            # 업데이트
            for key, value in profile_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return self.update(existing)
        else:
            # 생성
            new_profile = User(uuid=user_id, **profile_data)
            return self.create(new_profile)
    
    def get_all_profiles(self, skip: int = 0, limit: int = 100) -> List[User]:
        """전체 프로필 조회"""
        return self.get_all(skip=skip, limit=limit)
    
    def exists_by_user_id(self, user_id: str) -> bool:
        """사용자 프로필 존재 여부 확인"""
        stmt = select(User).where(User.uuid == user_id)
        result = self.db.execute(stmt).scalars().first()
        return result is not None

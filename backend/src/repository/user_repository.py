"""User Repository - 사용자 데이터 접근 계층"""
from typing import Optional
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.entity.user import User
from src.repository.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """사용자 Repository (프로필 + 벡터 관리)"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_uuid(self, uuid: str) -> Optional[User]:
        """UUID로 사용자 조회"""
        stmt = select(User).where(User.uuid == uuid)
        return self.db.execute(stmt).scalars().first()

    def ensure_user(self, uuid: str) -> User:
        """사용자 없으면 생성, 있으면 반환"""
        user = self.get_by_uuid(uuid)
        if user is None:
            user = User(
                uuid=uuid,
                user_vector_json=json.dumps([]),
                vector_dirty_at=None,
                has_onboarded=False,
                onboarding_json=None,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def upsert_vector(self, uuid: str, vector_json: str) -> None:
        """벡터 저장 (upsert)"""
        user = self.get_by_uuid(uuid)
        if user is None:
            user = User(
                uuid=uuid,
                user_vector_json=vector_json,
                vector_dirty_at=None,
                updated_at=datetime.utcnow(),
            )
            self.db.add(user)
        else:
            user.user_vector_json = vector_json
            user.vector_dirty_at = None  # dirty 해제
            user.updated_at = datetime.utcnow()
        self.db.commit()

    def mark_vector_dirty(self, uuid: str) -> None:
        """벡터 재계산 필요 표시"""
        user = self.ensure_user(uuid)
        now = datetime.utcnow()
        if user.vector_dirty_at is None:
            user.vector_dirty_at = now
        user.updated_at = now
        self.db.commit()

    def is_vector_dirty(self, uuid: str) -> bool:
        """벡터 재계산 필요 여부"""
        user = self.get_by_uuid(uuid)
        if user is None:
            return False
        return user.vector_dirty_at is not None

    def set_onboarding(self, uuid: str, answers: dict) -> User:
        """온보딩 완료 처리"""
        user = self.ensure_user(uuid)
        user.has_onboarded = True
        user.onboarding_json = answers
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def exists_by_uuid(self, uuid: str) -> bool:
        """사용자 존재 여부"""
        return self.get_by_uuid(uuid) is not None

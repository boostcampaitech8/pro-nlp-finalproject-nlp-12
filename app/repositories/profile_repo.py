from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user_profile import UserProfile


class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: str) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return self.db.execute(stmt).scalars().first()

    # 프로필 row 없으면 생성만 보장
    def ensure_profile(self, user_id: str) -> UserProfile:
        prof = self.get(user_id)
        if prof is None:
            prof = UserProfile(
                user_id=user_id,
                user_vector_json=json.dumps([]),   # TEXT 안전 기본값
                vector_dirty_at=None,
                updated_at=datetime.utcnow(),
                has_onboarded=False,
                onboarding_json=None,
            )
            self.db.add(prof)
            self.db.commit()
            self.db.refresh(prof)
        return prof

    def upsert(self, user_id: str, user_vector_json: str) -> None:
        prof = self.get(user_id)
        if prof is None:
            prof = UserProfile(
                user_id=user_id,
                user_vector_json=user_vector_json,
                vector_dirty_at=None,
                updated_at=datetime.utcnow(),
                has_onboarded=False,
                onboarding_json=None,
            )
            self.db.add(prof)
        else:
            prof.user_vector_json = user_vector_json
            prof.vector_dirty_at = None  # ✅ 벡터 갱신했으니 dirty 해제
            prof.updated_at = datetime.utcnow()
        self.db.commit()

    # dirty 표시만 (벡터 재계산은 하지 않음)
    def mark_vector_dirty(self, user_id: str) -> None:
        prof = self.get(user_id)
        now = datetime.utcnow()
    
        if prof is None:
            prof = UserProfile(
                user_id=user_id,
                user_vector_json=json.dumps([]),
                vector_dirty_at=now,
                updated_at=now,
                has_onboarded=False,
                onboarding_json=None,
            )
            self.db.add(prof)
        else:
            # ✅ 핵심: NULL일 때만 dirty 찍기 (이미 dirty면 타임스탬프 유지)
            if prof.vector_dirty_at is None:
                prof.vector_dirty_at = now
            prof.updated_at = now
    
        self.db.commit()

    def is_vector_dirty(self, user_id: str) -> bool:
        prof = self.get(user_id)
        if prof is None:
            return False
        return prof.vector_dirty_at is not None

    # 온보딩 저장 + 완료 처리
    def set_onboarding(self, user_id: str, answers: dict) -> UserProfile:
        prof = self.ensure_profile(user_id)
        prof.has_onboarded = True
        prof.onboarding_json = answers   
        prof.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(prof)
        return prof

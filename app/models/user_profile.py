from sqlalchemy import Column, BigInteger, String, DateTime, Text, func, Index, Boolean, JSON
from app.models.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String(64), primary_key=True)

    # JSON 문자열로 저장 (list[float])
    user_vector_json = Column(Text, nullable=True)

    # dirty flag
    vector_dirty_at = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    has_onboarded = Column(Boolean, nullable=False, default=False)
    onboarding_json = Column(JSON, nullable=True)

Index("ix_user_profiles_updated", UserProfile.updated_at)
Index("ix_user_profiles_vector_dirty", UserProfile.vector_dirty_at)

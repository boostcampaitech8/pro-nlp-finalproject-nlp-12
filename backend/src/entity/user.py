from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text, JSON, func, Boolean
from datetime import datetime
from typing import Optional, List

class User(Base):
    """
    사용자 정보를 관리하는 엔티티입니다.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    
    uuid: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    user_vector_json: Mapped[Optional[str]] = mapped_column(Text)
    vector_dirty_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    has_onboarded: Mapped[Optional[bool]] = mapped_column(Boolean)
    onboarding_json: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user_events : Mapped[List["UserEvent"]] = relationship(
        "UserEvent",
        back_populates="user",
        cascade="all, delete-orphan"
    )
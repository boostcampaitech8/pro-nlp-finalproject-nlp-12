from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, String, ForeignKey, func
from datetime import datetime
from src.entity.base import Base
from typing import TYPE_CHECKING

# 실행 시점에는 타입체크 시점만 참조(순환 참조 방지)
if TYPE_CHECKING:
    from src.entity.paper import Paper
    from src.entity.user import User


class UserEvent(Base):
    """
    좋아요/북마크/클릭 등 이벤트 관리 엔티티
    """
    __tablename__ = "user_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True
    )

    # 관계 설정
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_events"
    )
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="user_events"
    )

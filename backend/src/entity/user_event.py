from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum
from datetime import datetime
from src.entity.base import Base
import enum
from typing import TYPE_CHECKING

# 실행 시점이 아닌 타입 체크 시점에만 참조(순환 참조 방지)
if TYPE_CHECKING:
    from src.entity.paper import Paper
    from src.entity.user import User

class EventType(enum.Enum):
    like = "like"          # 좋아요
    bookmark = "bookmark"  # 북마크
    click = "click"        # 자세히 보기 클릭
    impression = "impression"  # 노출 (seen)

class UserEvent(Base):
    """
    좋아요 및 북마크를 관리하는 엔티티입니다.
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
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, native_enum=False),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
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
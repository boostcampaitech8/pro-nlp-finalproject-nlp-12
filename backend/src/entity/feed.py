from src.entity.base import Base
from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class Feed(Base):
    """
    피드를 관리하는 엔티티입니다.
    """
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # 추후 Enum으로 수정해야 함
    feed_type: Mapped[str] = Column(
        Text,
        nullable=False
    )
    contents: Mapped[str] = Column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 관계 설정
    paper: Mapped["Paper"] = relationship(back_populates="feeds")
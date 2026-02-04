from sqlalchemy import Integer, String, Text, Date, DateTime, func
from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

# 실행 시점이 아닌 타입 체크 시점에만 참조(순환 참조 방지)
if TYPE_CHECKING:
    from src.entity.user_event import UserEvent
    from src.entity.citation_edge import CitationEdge
    from src.entity.feed import Feed
    from src.entity.summary import Summary
    from src.entity.primary_category import PrimaryCategory
    from src.entity.paper_category import PaperCategory

class Paper(Base):
    """
    논문 정보를 관리하는 엔티티입니다.
    """
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    arxiv_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(String(1000))
    abstract: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    citation_count: Mapped[Optional[int]] = mapped_column(Integer)
    influential_citation_count: Mapped[Optional[int]] = mapped_column(Integer)
    reference_count: Mapped[Optional[int]] = mapped_column(Integer)
    published_date: Mapped[Optional[date]] = mapped_column(Date)
    updated_date: Mapped[Optional[date]] = mapped_column(Date)

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

    # 관계 설정
    user_events: Mapped[List["UserEvent"]] = relationship(
        "UserEvent",
        back_populates="paper",
        cascade="all, delete-orphan"
    )
    summaries: Mapped[List["Summary"]] = relationship(
        "Summary",
        back_populates="paper",
        cascade="all, delete-orphan"
    )
    feeds: Mapped[List["Feed"]] = relationship(
        "Feed",
        back_populates="paper",
        cascade="all, delete-orphan"
    )
    citations_out: Mapped[List["CitationEdge"]] = relationship(
        "CitationEdge",
        foreign_keys="[CitationEdge.seed_id]",
        back_populates="citing_paper",
        cascade="all, delete-orphan"
    )
    citations_in: Mapped[List["CitationEdge"]] = relationship(
        "CitationEdge",
        foreign_keys="[CitationEdge.cited_paper_id]",
        back_populates="cited_paper",
        cascade="all, delete-orphan"
    )
    paper_categories: Mapped[List["PaperCategory"]] = relationship(
        "PaperCategory", 
        back_populates="paper",
        cascade="all, delete-orphan"
    )
    primary_category: Mapped["PrimaryCategory"] = relationship(
        "PrimaryCategory", 
        back_populates="paper",
        cascade="all, delete-orphan"
    )
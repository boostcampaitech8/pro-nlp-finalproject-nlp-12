from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, DateTime, func, ForeignKey, Enum
from datetime import datetime
import enum

class SummaryType(enum.Enum):
    motivation = "motivation"      # 연구 배경 및 문제 의식
    methodology = "methodology"    # 주요 방법론
    performance = "performance"    # 실험 및 성과
    significance = "significance"  # 의의 및 향후 영향력

class Summary(Base):
    """
    논문 요약 결과를 관리하는 엔티티입니다.
    """
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id"),
        nullable=False,
        index=True
    )
    summary_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    summary_type: Mapped[SummaryType] = mapped_column(
        Enum(SummaryType),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    paper: Mapped["Paper"] = relationship(back_populates="summaries")
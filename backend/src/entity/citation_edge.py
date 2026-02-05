from src.entity.base import Base
from sqlalchemy import Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

# 실행 시점이 아닌 타입 체크 시점에만 참조(순환 참조 방지)
if TYPE_CHECKING:
    from src.entity.paper import Paper

class CitationEdge(Base):
    """
    논문의 인용 관계를 관리하는 엔티티입니다.
    """
    __tablename__ = "citation_edges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    seed_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    cited_paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_influential: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 데이터 무결성을 위한 코드 추가
    __table_args__ = (
        UniqueConstraint("seed_id", "cited_paper_id", name="_seed_cited_uc"),
    )

    # 관계 설정
    citing_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[seed_id],
        back_populates="citations_out"
    )

    cited_paper: Mapped["Paper"] = relationship(
        "Paper",
        foreign_keys=[cited_paper_id],
        back_populates="citations_in"
    )
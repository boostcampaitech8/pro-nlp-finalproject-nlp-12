from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, UniqueConstraint

class PaperCategory(Base):
    """
    논문별 카테고리를 관리하는 엔티티입니다.
    """
    __tablename__ = "papers_categories"

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
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 데이터 무결성을 위한 코드 추가
    __table_args__ = (
        UniqueConstraint("paper_id", "category_id", name="_paper_category_uc"),
    )

    # 관계 설정
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="paper_categories"
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="paper_categories"
    )
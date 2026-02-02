from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey

class PrimaryCategory(Base):
    """
    논문별 대표 카테고리를 관리하는 엔티티입니다.
    """
    __tablename__ = "primary_categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 관계 설정
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="primary_category"
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="primary_categories"
    )
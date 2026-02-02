from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, UniqueConstraint

class UserPaperCategory(Base):
    """
    사용자가 선택한 카테고리를 관리하는 엔티티입니다.
    """
    __tablename__ = "user_paper_categories"

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
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 데이터 무결성을 위한 코드 추가
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="_user_category_uc"),
    )

    # 관계 설정
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_paper_categories"
    )
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="user_paper_categories"
    )
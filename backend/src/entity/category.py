from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from typing import List, TYPE_CHECKING

# 실행 시점이 아닌 타입 체크 시점에만 참조(순환 참조 방지)
if TYPE_CHECKING:
    from src.entity.paper_category import PaperCategory
    from src.entity.primary_category import PrimaryCategory
    from src.entity.user_paper_category import UserPaperCategory

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    category_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True
    )

    # 관계 설정
    paper_categories: Mapped[List["PaperCategory"]] = relationship(
        "PaperCategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )
    primary_categories: Mapped[List["PrimaryCategory"]] = relationship(
        "PrimaryCategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )
    user_paper_categories: Mapped[List["UserPaperCategory"]] = relationship(
        "UserPaperCategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )
from src.entity.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String

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
    paper_categories: Mapped[list["PaperCategory"]] = relationship(
        "PaperCategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )
    primary_categories: Mapped[list["PrimaryCategory"]] = relationship(
        "PrimaryCategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )
    user_paper_categories: Mapped[list["UserPaperCategory"]] = relationship(
        "UserPaperCategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )
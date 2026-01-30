from sqlalchemy import Column, Integer, String, Text, DateTime
from src.entity.base import Base

class Paper(Base):
    __tablename__ = "papers_nlp_transformer"

    id = Column(Integer, primary_key=True, autoincrement=True)

    arxiv_id = Column(String(64), nullable=False, index=True)  # MUL
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=False)
    authors = Column(Text, nullable=False)

    primary_category = Column(String(64), nullable=True)
    categories = Column(Text, nullable=True)

    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    abs_url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False)

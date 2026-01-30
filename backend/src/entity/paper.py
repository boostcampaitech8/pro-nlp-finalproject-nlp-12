from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func
from . import Base
from sqlalchemy.orm import relationship

class Paper(Base):
    """
    논문 정보를 관리하는 엔티티입니다.
    """
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arxiv_id = Column(String(50), unique=True, index=False)
    title = Column(String(500), nullable=False)
    pdf_url = Column(String(1000))
    abstract = Column(Text)

    citation_count = Column(Integer)
    influential_citation_count = Column(Integer)
    reference_count = Column(Integer)
    published_date = Column(Date)
    updated_date = Column(Date)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    summaries = relationship("Summary", back_populates="papers")
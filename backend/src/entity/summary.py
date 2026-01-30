from . import Base
from sqlalchemy import Column, Integer, Text, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

class Summary(Base):
    """
    논문 요약 결과를 관리하는 엔티티입니다.
    """
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)

    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    summary_type = Column(String(50))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    papers = relationship("Paper", back_populates="summaries")
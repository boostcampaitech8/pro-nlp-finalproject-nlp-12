from . import Base
from sqlalchemy import Column, Integer, ForeignKey, Boolean, UniqueConstraint

class CitationEdge(Base):
    """
    논문의 인용 관계를 관리하는 엔티티입니다.
    """
    __tablename__ = "citation_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)

    seed_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    cited_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    is_influential = Column(Boolean)

    # 데이터 무결성을 위한 코드 추가
    __table_args__ = (
        UniqueConstraint("seed_id", "cited_paper_id", name="_seed_cited_uc"),
    )
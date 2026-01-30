from . import Base
from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, Text

class Feed(Base):
    """
    피드를 관리하는 엔티티입니다.
    """
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, autoincrement=True)

    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    feed_type = Column(Text, nullable=False)
    contents = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
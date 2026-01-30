from sqlalchemy import Column, BigInteger, String, DateTime, Float, Index, func, Integer
from src.entity.base import Base

class UserEvent(Base):
    __tablename__ = "user_events"

    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)

    paper_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(32), nullable=False)
    weight = Column(Float, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

Index("ix_user_events_user_paper", UserEvent.user_id, UserEvent.paper_id)

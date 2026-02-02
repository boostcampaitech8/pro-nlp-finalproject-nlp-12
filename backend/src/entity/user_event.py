from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, TIMESTAMP
from datetime import datetime
from . import Base

class UserEvent(Base):
    __tablename__ = "user_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    paper_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=1)  ### 수정사항: click 횟수 저장용 컬럼 추가
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default="CURRENT_TIMESTAMP"
    )

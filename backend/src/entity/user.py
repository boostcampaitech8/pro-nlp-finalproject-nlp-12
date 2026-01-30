from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, JSON
from datetime import datetime
from typing import Optional
from . import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default="CURRENT_TIMESTAMP"
    )

    survey_categories: Mapped[Optional[str]] = mapped_column(Text)
    survey_paper_ids: Mapped[Optional[str]] = mapped_column(Text)
    extracted_keywords: Mapped[Optional[str]] = mapped_column(Text)
    preference_query: Mapped[Optional[str]] = mapped_column(Text)
    user_vector_json: Mapped[Optional[str]] = mapped_column(Text)

    vector_dirty_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    has_onboarded: Mapped[Optional[bool]] = mapped_column(Integer)
    onboarding_json: Mapped[Optional[dict]] = mapped_column(JSON)

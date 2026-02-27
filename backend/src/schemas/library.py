from datetime import datetime
from pydantic import BaseModel


class LibraryItem(BaseModel):
    paper_id: int
    event_type: str               # "like" | "bookmark"
    created_at: datetime

    title: str | None = None
    summary: str | None = None
    abs_url: str | None = None
    pdf_url: str | None = None
    published_at: datetime | None = None

    primary_category: str | None
    categories: str | None


class LibraryResponse(BaseModel):
    user_id: str
    type: str                     # like/bookmark/all
    limit: int
    offset: int
    total: int
    items: list[LibraryItem]

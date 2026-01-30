# Auto-generated entity module
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy Base class for all entities"""
    pass


from .paper import Paper
from .user import User
from .user_event import UserEvent
from .summary import Summary
from .feed import Feed
from .citation_edge import CitationEdge

__all__ = [
    "Base",
    "Paper",
    "User",
    "UserEvent",
    "Summary",
    "Feed",
    "CitationEdge",
]

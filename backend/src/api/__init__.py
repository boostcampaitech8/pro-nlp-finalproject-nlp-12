"""API Routers"""

from src.api.feed import router as feed_router
from src.api.survey import router as survey_router
from src.api.events import router as events_router
from src.api.admin import router as admin_router
from src.api.library import router as library_router
from src.api.paper import router as paper_router
from src.api.search import router as search_router

__all__ = [
    "feed_router",
    "survey_router",
    "events_router",
    "admin_router",
    "library_router",
    "paper_router",
    "search_router",
]

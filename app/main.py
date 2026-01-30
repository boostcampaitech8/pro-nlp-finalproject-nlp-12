from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import engine
from app.models.base import Base
from app.models.user_event import UserEvent  # noqa: F401
from app.models.user_profile import UserProfile  # noqa: F401
from app.models.paper import Paper  # noqa: F401
from app.routers import users

from app.routers.admin import router as admin_router
from app.routers.events import router as events_router
from app.routers.feed import router as feed_router
from app.routers.debug import router as debug_router
from app.routers.library import router as library_router
from app.routers.search import router as search_router

app = FastAPI(title="paper_short")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

API_PREFIX = "/api"

app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(feed_router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(debug_router, prefix=API_PREFIX)
app.include_router(library_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)

@app.get("/health")
def health():
    return {"ok": True}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# DB 초기화
from src.database.mysql import engine
from src.entity.base import Base
import src.entity  # noqa: F401


# 모든 모델 import (metadata 인식용) create_all 안하니깐 일단은 주석처리
# from src.entity.user_event import UserEvent  # noqa
# from src.entity.user_profile import UserProfile  # noqa
# from src.entity.paper import Paper  # noqa

from src.api.user import router as user_router
from src.api.paper import router as paper_router

from src.api.admin import router as admin_router
from src.api.events import router as events_router
from src.api.feed import router as feed_router
from src.api.library import router as library_router
from src.api.search import router as search_router
from src.api.user import router as user_router
from src.api.paper import router as paper_router

app = FastAPI(
    title="10seconds",
    description="논문 요약 및 숏폼 추천 API 서버"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

API_PREFIX = "/api"

app.include_router(user_router)
app.include_router(paper_router, prefix=API_PREFIX)

app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(feed_router, prefix=API_PREFIX)
app.include_router(library_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)

@app.get("/")
def read_root():
    return {"message": "논문 숏폼 서비스입니다."}

@app.get("/health")
def health():
    return {"ok": True}

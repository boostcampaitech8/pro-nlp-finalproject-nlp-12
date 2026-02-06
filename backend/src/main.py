from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api import search, summary, admin, events, feed, library, users
from src.client.faiss_store import get_faiss_store
from src.repository.paper_repo import PaperRepository
from src.entity.base import init_db
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB 초기화
    init_db()

    # 서버 시작 시 초기 데이터 로딩
    from src.database.mysql import get_mysql_db

    db_gen = get_mysql_db()
    db = next(db_gen)  # generator에서 세션을 수동으로 꺼냄

    try:
        # 논문 가져오기
        paper_repository = PaperRepository(db)
        all_papers = paper_repository.get_papers_as_documents()

        # Faiss 인스턴스 생성 및 신규 논문 업데이트
        faiss_store = get_faiss_store()
        faiss_store.update_papers(all_papers)

        app.state.faiss_store = faiss_store
        app.state.all_papers = all_papers
    finally:
        # 세션 반환
        try:
            next(db_gen)
        except StopIteration:
            pass

    yield

app = FastAPI(
    title="논문 숏폼 서비스",
    description="논문 요약 및 숏폼 추천 API 서버",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

API_PREFIX = "/api"

app.include_router(search.router, prefix=API_PREFIX)
app.include_router(summary.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(events.router, prefix=API_PREFIX)
app.include_router(feed.router, prefix=API_PREFIX)
app.include_router(library.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)

@app.get("/")
def read_root():
    return {"message": "논문 숏폼 서비스입니다."}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)

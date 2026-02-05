from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api import search, summary, admin, events, feed, library, users
from src.client.faiss_store import get_faiss_store
from src.service.paper_service import PaperService
from src.repository.paper_repo import PaperRepository
from src.entity.base import init_db
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB 초기화
    init_db()

    # 논문 가져오기
    all_papers = PaperRepository.get_papers_as_documents()

    # Faiss 인스턴스 생성 및 신규 논문 업데이트
    faiss_store = get_faiss_store(dim=1024, index_path="data/faiss/index.bin")
    faiss_store.update_papers(all_papers)

    # app.state에 서비스 인스턴스 저장(어디서든 꺼내 쓸 수 있음)
    app.state.paper_service = PaperService(faiss_store, all_papers)

    yield

app = FastAPI(
    title="논문 숏폼 서비스",
    description="논문 요약 및 숏폼 추천 API 서버",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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
    uvicorn.run("src.main:app", host="127.0.0.1", port=8080, reload=True)
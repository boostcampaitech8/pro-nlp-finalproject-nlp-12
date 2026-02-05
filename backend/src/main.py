from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import src.entity
from src.api import search, summary
from src.entity.base import init_db
from src.service.paper_service import PaperService
from src.service.faiss_service import faiss_service
from src.repository.paper_repository import PaperRepository
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB 초기화
    init_db()

    # 무거운 작업 처리
    all_papers = PaperRepository.get_papers_as_documents()
    faiss_service.update_papers(all_papers)

    # app.state에 서비스 인스턴스 저장(어디서든 꺼내 쓸 수 있음)
    app.state.paper_service = PaperService(faiss_service, all_papers)

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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(search.router)
app.include_router(summary.router)

@app.get("/")
def read_root():
    return {"message": "논문 숏폼 서비스입니다."}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8080, reload=True)
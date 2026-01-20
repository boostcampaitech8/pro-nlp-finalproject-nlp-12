from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.user import router as user_router
from src.api.paper import router as paper_router

app = FastAPI(
    title="논문 숏폼 서비스",
    description="논문 요약 및 숏폼 추천 API 서버"
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

app.include_router(user_router)
app.include_router(paper_router)

@app.get("/")
def read_root():
    return {"message": "논문 숏폼 서비스입니다."}
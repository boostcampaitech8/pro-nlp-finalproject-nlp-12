"""
FastAPI 애플리케이션 메인 진입점
논문 숏폼 추천 서비스 (MVP3)
"""
import logging
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.api import survey, feed, events

# ===== 로깅 설정 =====
os.makedirs(settings.LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(settings.LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# ===== FastAPI 앱 생성 =====
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## 주요 기능
    
    ### 1. 설문 (Survey)
    - GET /api/survey/categories - 카테고리 목록
    - POST /api/survey/categories - Step 1: 카테고리 저장
    - GET /api/survey/papers - Step 2: 논문 목록
    - POST /api/survey - Step 3: 설문 완료 + LLM 키워드 추출
    - GET /api/survey/profile/{user_id} - 프로필 조회
    
    ### 2. 피드 (Feed)
    - GET /api/feed - 개인화 추천 피드
    
    ### 3. 이벤트 (Events)
    - POST /api/events - 사용자 이벤트 기록
    - GET /api/events/user/{user_id} - 사용자 이벤트 조회
    """,
)

# ===== CORS 미들웨어 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 라우터 등록 =====
app.include_router(survey.router)
app.include_router(feed.router)
app.include_router(events.router)

# ===== Health Check =====
@app.get("/")
def read_root():
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

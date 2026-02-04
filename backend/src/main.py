"""
FastAPI 애플리케이션 메인 진입점
논문 숏폼 추천 서비스
"""
import logging
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
### 수정사항: 모든 엔티티 로드 (relationship 연결용)
from src.entity.base import init_db
init_db()

from src.api import (
    feed_router,
    survey_router,
    events_router,
    admin_router,
    library_router,
    paper_router,
    search_router,
)

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
    ## 논문 숏폼 추천 서비스 API

    ### 1. 설문/온보딩 (Survey)
    - GET /api/survey/categories - 카테고리 목록
    - POST /api/survey/categories - Step 1: 카테고리 저장
    - GET /api/survey/papers - Step 2: 논문 목록
    - POST /api/survey - Step 3: 설문 완료 + LLM 키워드 추출
    - GET /api/survey/profile/{user_id} - 프로필 조회

    ### 2. 피드 (Feed)
    - GET /api/feed - 빠른 추천 피드 (저장된 벡터 기반, 커서 페이지네이션)
    - GET /api/feed/slow - 느린 추천 피드 (LLM 실시간 쿼리 기반)

    ### 3. 이벤트 (Events)
    - POST /api/events - 사용자 이벤트 기록 (click, like, bookmark, impression, dislike)
    - GET /api/events/user/{user_id} - 사용자 이벤트 조회

    ### 4. 라이브러리 (Library)
    - GET /api/me/library - 좋아요/북마크 목록

    ### 5. 검색 (Search)
    - GET /api/search - FAISS 벡터 검색

    ### 6. 논문 상세 (Paper)
    - GET /api/paper/{paper_id} - 논문 상세 정보

    ### 7. 관리자 (Admin)
    - POST /api/admin/sync - DB → FAISS 동기화
    - POST /api/admin/reindex_faiss_all - FAISS 전체 재인덱싱
    - GET /api/admin/stats - 시스템 통계
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
# 모든 라우터에 이미 prefix가 포함되어 있음
app.include_router(survey_router)
app.include_router(feed_router)
app.include_router(events_router)
app.include_router(library_router)
app.include_router(paper_router)
app.include_router(search_router)
app.include_router(admin_router)


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
    return {"status": "healthy", "ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

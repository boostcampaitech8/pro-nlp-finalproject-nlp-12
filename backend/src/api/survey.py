"""설문 API - 카테고리 선택 → 논문 선택 → LLM 처리"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_

from src.database.mysql import get_db
from src.utils.rate_limiter import check_rate_limit
from src.entity.paper import Paper
from src.entity.user import User
from src.schemas.survey import (
    CategorySelectRequest,
    CategorySelectResponse,
    SurveyPapersResponse,
    PaperForSelection,
    SurveyCompleteRequest,
    SurveyCompleteResponse,
    ProfileResponse,
    ARXIV_CATEGORIES,
)
from src.service.preference_service import PreferenceService
from src.repository.paper_repository import PaperRepository

router = APIRouter(prefix="/api/survey", tags=["survey"])


@router.get("/categories")
def get_categories():
    """선택 가능한 카테고리 목록"""
    return {"categories": ARXIV_CATEGORIES}


@router.post("/categories", response_model=CategorySelectResponse)
def save_categories(payload: CategorySelectRequest, db: Session = Depends(get_db)):
    """
    Step 1: 카테고리 저장
    프로필을 생성하거나 업데이트
    """
    service = PreferenceService(db)
    service.save_categories(payload.user_id, payload.categories)
    
    return CategorySelectResponse(
        ok=True,
        user_id=payload.user_id,
        categories=payload.categories,
    )


@router.get("/papers", response_model=SurveyPapersResponse)
def get_survey_papers(
    categories: str = Query(..., description="쉼표로 구분된 카테고리"),
    limit: int = Query(default=50, ge=10, le=200),
    db: Session = Depends(get_db),
):
    """
    Step 2: 설문용 논문 목록
    카테고리 선택 후 선택할 논문들을 가져옴
    """
    try:
        paper_repo = PaperRepository(db)
        category_list = [c.strip() for c in categories.split(",")]
        
        # Repository를 통한 논문 조회
        papers = paper_repo.get_by_categories_with_citations(
            categories=category_list,
            min_citations=1,
            limit=limit
        )
        
        items = [
            PaperForSelection(
                paper_id=p.id,
                arxiv_id=p.arxiv_id,
                title=p.title,
                abstract=p.abstract or "",
                authors=None,  # 새 엔티티에 authors 필드 없음
                primary_category=None,  # 새 엔티티에 없음
                citation_count=p.citation_count or 0,
                published_at=p.published_date.isoformat() if p.published_date else None,
            )
            for p in papers
        ]
        
        return SurveyPapersResponse(papers=items, total=len(items))
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=SurveyCompleteResponse)
def complete_survey(
    payload: SurveyCompleteRequest,
    db: Session = Depends(get_db),
):
    """
    Step 3: 설문 완료
    카테고리 + 논문 선택 저장 후 LLM으로 키워드 추출
    """
    ### 수정사항: Rate limit 추가 (분당 2회)
    check_rate_limit(payload.user_id, action="survey", max_requests=2, window_minutes=1)

    try:
        service = PreferenceService(db)
        
        # 1. 논문 선택 저장
        service.save_papers(payload.user_id, payload.categories, payload.paper_ids)
        
        # 2. LLM으로 키워드 추출
        keywords = service.extract_keywords_from_papers(payload.paper_ids)
        
        # 3. Preference 벡터 생성 및 저장
        service.generate_preference_vector(
            user_id=payload.user_id,
            categories=payload.categories,
            paper_ids=payload.paper_ids,
            extracted_keywords=keywords,
        )
        
        return SurveyCompleteResponse(
            ok=True,
            user_id=payload.user_id,
            categories=payload.categories,
            paper_ids=payload.paper_ids,
            extracted_keywords=keywords,
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: str, db: Session = Depends(get_db)):
    """사용자 프로필 조회"""
    service = PreferenceService(db)
    profile = service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="프로필을 찾을 수 없습니다")
    
    return ProfileResponse(**profile)

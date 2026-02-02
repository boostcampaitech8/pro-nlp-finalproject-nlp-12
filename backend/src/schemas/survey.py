"""설문 관련 요청/응답 스키마"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# arXiv 카테고리
ARXIV_CATEGORIES = [
    "cs.AI",          # Artificial Intelligence
    "cs.LG",          # Machine Learning
    "cs.NE",          # Neural and Evolutionary Computing
    "cs.CV",          # Computer Vision
    "cs.CL",          # Computation and Language
    "stat.ML",        # Machine Learning (Statistics)
]


# ===== Step 1: 카테고리 선택 =====
class CategorySelectRequest(BaseModel):
    """카테고리 선택 요청"""
    user_id: str = Field(..., min_length=1)
    categories: list[str] = Field(..., min_length=1, description="최소 1개 카테고리 필수")


class CategorySelectResponse(BaseModel):
    """카테고리 선택 응답"""
    ok: bool
    user_id: str
    categories: list[str]


# ===== Step 2: 논문 선택 =====
class PaperForSelection(BaseModel):
    """설문용 논문 정보"""
    paper_id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: Optional[str] = None
    primary_category: Optional[str] = None
    citation_count: int = 0
    published_at: Optional[str] = None


class SurveyPapersResponse(BaseModel):
    """설문용 논문 목록 응답"""
    papers: list[PaperForSelection]
    total: int


# ===== Step 3: 설문 완료 =====
class SurveyCompleteRequest(BaseModel):
    """설문 완료 요청"""
    user_id: str = Field(..., min_length=1)
    categories: list[str] = Field(..., min_length=1)
    paper_ids: list[int] = Field(default=[], description="선택한 논문 ID (선택 사항)")  ### 수정사항: 논문 선택 필수 → 선택사항으로 변경


class SurveyCompleteResponse(BaseModel):
    """설문 완료 응답"""
    ok: bool
    user_id: str
    categories: list[str]
    paper_ids: list[int]
    extracted_keywords: list[str]


# ===== 프로필 조회 =====
class ProfileResponse(BaseModel):
    """사용자 프로필 응답"""
    user_id: str
    categories: list[str]
    paper_ids: list[int]
    keywords: list[str]
    preference_query: Optional[str] = None
    has_vector: bool
    updated_at: Optional[str] = None

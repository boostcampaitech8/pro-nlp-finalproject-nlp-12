from pydantic import BaseModel, HttpUrl
from src.entity.summary import SummaryType
from typing import List

class SummaryRequest(BaseModel):
    """
    논문 요약 요청을 관리하는 스키마입니다.
    """
    user_id: str
    paper_id: int

class SummaryDetail(BaseModel):
    summary_type: SummaryType
    summary_text: str

class SummaryResponse(BaseModel):
    """
    논문 요약 결과를 관리하는 스키마입니다.
    """
    paper_id: int
    pdf_url: HttpUrl
    abs_url: HttpUrl
    summaries: List[SummaryDetail]
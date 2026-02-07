from pydantic import BaseModel, HttpUrl, Field
from src.entity.summary import SummaryType
from typing import List, Optional

class SummaryRequest(BaseModel):
    """
    논문 요약 요청을 관리하는 스키마입니다.
    """
    user_id: str
    paper_id: Optional[int] = Field(
        default=None,
        description="논문 내부 데이터베이스 ID(선택)",
        json_schema_extra={"default": None}
    )
    arxiv_id: Optional[str] = Field(
        default=None,
        description="Arxiv 고유 식별 코드 (선택)",
        json_schema_extra={"default": None}
    )

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
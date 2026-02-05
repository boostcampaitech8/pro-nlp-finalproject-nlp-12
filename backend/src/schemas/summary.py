from pydantic import BaseModel
from src.entity.summary import SummaryType

class SummaryRequest(BaseModel):
    """
    논문 요약 요청을 관리하는 스키마입니다.
    """
    user_id: str
    paper_id: int

class SummaryResponse(BaseModel):
    """
    논문 요약 결과를 관리하는 스키마입니다.
    """
    paper_id: int
    summary_type: SummaryType
    summary_text: str
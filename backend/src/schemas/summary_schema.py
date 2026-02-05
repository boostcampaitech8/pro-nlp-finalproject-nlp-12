from pydantic import BaseModel
from src.entity.summary import SummaryType

class SummaryRequest(BaseModel):
    user_id: int
    paper_id: int

class SummaryResponse(BaseModel):
    paper_id: int
    summary_type: SummaryType
    summary_text: str
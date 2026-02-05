from pydantic import BaseModel, HttpUrl
from datetime import date

class SearchRequest(BaseModel):
    """
    논문 검색 요청을 관리하는 스키마입니다.
    """
    user_id: str
    query: str
    
class SearchResponse(BaseModel):
    """
    논문 검색 결과를 관리하는 스키마입니다.
    """
    paper_id: int
    arxiv_id: str
    title: str
    pdf_url: HttpUrl
    abs_url: HttpUrl
    published_date: date
    summary: str
    is_liked: bool
    is_bookmarked: bool
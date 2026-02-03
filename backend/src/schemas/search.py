from pydantic import BaseModel, HttpUrl

class SearchResponse(BaseModel):
    """
    논문 검색 결과를 관리하는 스키마입니다.
    """
    arxiv_id: str
    title: str
    abstract: str
    pdf_url: HttpUrl

    score: float
    sparse_rank: int
    dense_rank: int
    final_rank: int
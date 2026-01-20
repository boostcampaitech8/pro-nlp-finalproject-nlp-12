from pydantic import BaseModel

class LikeRequest(BaseModel):
    session_id: str
    arxiv_id: str

class LikeResponse(BaseModel):
    is_liked: bool

class PaperResponse(BaseModel):
    arxiv_id: str
    title: str
    abstract: str
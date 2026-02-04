"""Client 모듈 - 외부 API 클라이언트 및 벡터 저장소"""
from src.client.arxiv_client import ArxivClient
from src.client.s2_client import SemanticScholarClient
from src.client.faiss_store import FaissStore, get_faiss_store
from src.client.embedder import get_model, embed_texts, embed_single

__all__ = [
    "ArxivClient",
    "SemanticScholarClient",
    "FaissStore",
    "get_faiss_store",
    "get_model",
    "embed_texts",
    "embed_single",
]

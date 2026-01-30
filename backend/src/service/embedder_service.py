from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
from typing import Optional
from src.config.settings import settings

_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """임베딩 모델 싱글톤 반환"""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """텍스트 리스트를 임베딩 벡터로 변환"""
    model = get_model()
    embeddings = model.encode(
        texts, 
        convert_to_numpy=True, 
        normalize_embeddings=True
    )
    return embeddings.astype(np.float32)


def embed_single(text: str) -> np.ndarray:
    """단일 텍스트를 임베딩 벡터로 변환"""
    return embed_texts([text])[0]

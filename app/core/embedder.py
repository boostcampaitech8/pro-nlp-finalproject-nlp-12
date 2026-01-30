from sentence_transformers import SentenceTransformer
from app.core.config import settings

_model = None

def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBED_MODEL)
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    # normalize_embeddings=True -> cosine 유사도 검색에 유리
    vecs = model.encode(texts, normalize_embeddings=True)
    return vecs.tolist()

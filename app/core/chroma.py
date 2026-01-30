import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

_client = None
_collections = {}  # name -> collection 캐시

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client

def get_collection(name: str | None = None):
    """
    컬렉션 이름별로 캐시
    - name이 None이면 settings.CHROMA_COLLECTION 사용
    """
    client = get_chroma_client()
    col_name = name or settings.CHROMA_COLLECTION

    col = _collections.get(col_name)
    if col is None:
        col = client.get_or_create_collection(name=col_name)
        _collections[col_name] = col
    return col

def reset_collection(name: str | None = None):
    """
    특정 컬렉션만 삭제/재생성
    """
    client = get_chroma_client()
    col_name = name or settings.CHROMA_COLLECTION
    try:
        client.delete_collection(name=col_name)
    except Exception:
        pass

    col = client.get_or_create_collection(name=col_name)
    _collections[col_name] = col
    return col

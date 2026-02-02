from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # ===== Database =====
    DB_URL: str = "mysql+pymysql://admin:password@localhost:3306/paper_db"
    
    # ===== FAISS Index =====
    FAISS_INDEX_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "faiss_index"
    )
    
    # ===== Embedding Model =====
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # ===== External APIs =====
    # Semantic Scholar API
    S2_API_KEY: str = ""
    S2_API_URL: str = "https://api.semanticscholar.org/graph/v1"
    
    # Groq LLM API
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TIMEOUT: int = 30
    
    # arXiv API
    ARXIV_API_URL: str = "http://export.arxiv.org/api/query"
    ARXIV_BATCH_SIZE: int = 100
    
    # ===== Redis/Cache =====
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1 hour
    
    # ===== CORS =====
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # ===== Logging =====
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "logs"
    )
    
    # ===== App Settings =====
    APP_NAME: str = "논문 숏폼 추천 시스템"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()


settings = get_settings()

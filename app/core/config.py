from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str

    CHROMA_HOST: str = "127.0.0.1"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION: str = "papers_embed_v1"

    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"

settings = Settings()

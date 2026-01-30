from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Embedding
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # FAISS
    EMBED_DIM: int = 384
    FAISS_INDEX_PATH: str = "data/faiss/index.bin"

    class Config:
        env_file = ".env"


settings = Settings()

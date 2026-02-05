from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # .env
    s2_api_key: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_db: str
    clovastudio_api_key: str

    # Embedding
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # FAISS
    EMBED_DIM: int = 384
    FAISS_INDEX_PATH: str = "data/faiss/index.bin"

    class Config:
        env_file = ".env"


settings = Settings()

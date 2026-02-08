from dotenv import load_dotenv
import os
from redis import asyncio

load_dotenv()

VALKEY_URI = os.getenv("VALKEY_URI")

valkey_pool = asyncio.ConnectionPool.from_url(
    VALKEY_URI,
    decode_responses=True,
    ssl_cert_reqs=None
)

# 싱글톤
valkey_client = asyncio.Redis(connection_pool=valkey_pool)

def get_valkey_db():
    """
    Valkey(Redis) 클라이언트를 반환합니다.
    """
    return valkey_client
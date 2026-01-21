from dotenv import load_dotenv
import os
import redis

load_dotenv()

VALKEY_HOST=os.getenv("VALKEY_HOST")
VALKEY_PORT=int(os.getenv("VALKEY_PORT"))
VALKEY_PASSWORD=os.getenv("VALKEY_PASSWORD")

valkey_client = redis.Redis(
    host=VALKEY_HOST,
    port=VALKEY_PORT,
    password=VALKEY_PASSWORD,
    decode_responses=True,  # 데이터를 "str"로 반환하기 위함
    ssl=True,
    ssl_cert_reqs=None
)

def get_valkey_db():
    """
    Valkey(Redis) 클라이언트를 반환합니다.
    """
    return valkey_client
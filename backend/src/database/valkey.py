from dotenv import load_dotenv
import os
import redis
from contextlib import contextmanager

load_dotenv()

VALKEY_HOST=os.getenv("VALKEY_HOST")
VALKEY_PORT=int(os.getenv("VALKEY_PORT"))
VALKEY_PASSWORD=os.getenv("VALKEY_PASSWORD")

@contextmanager
def get_valkey_db():
    """
    Valkey(Redis) 연결을 생성하고 사용 후 안전하게 닫습니다.
    """
    db = redis.Redis(
        host=VALKEY_HOST,
        port=VALKEY_PORT,
        password=VALKEY_PASSWORD,
        decode_responses=True,  # 데이터를 "str"로 반환하기 위함
        ssl=True,
        ssl_cert_reqs=None
    )

    try:
        yield db
    finally:
        db.close()
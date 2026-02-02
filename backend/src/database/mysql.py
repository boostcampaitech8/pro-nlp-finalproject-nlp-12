from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

load_dotenv()

# 환경 변수 로드
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# SQLAlchemy용 데이터베이스 URL 생성
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"

# Engine 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # 연결 유효성 체크
)

# 세션 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_mysql_db():
    """
    MySQL 연결을 생성하고 사용 후 안전하게 닫습니다.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
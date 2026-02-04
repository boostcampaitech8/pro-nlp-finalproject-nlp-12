"""MySQL 데이터베이스 연결 설정"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config.settings import settings

# SQLAlchemy Engine 생성
engine = create_engine(
    settings.DB_URL,
    pool_pre_ping=True,         # 연결 유효성 체크
    pool_recycle=3600,          # 1시간마다 연결 재설정
    echo=settings.DEBUG,        # DEBUG 모드에서 SQL 로깅
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    의존성 주입용 데이터베이스 세션 제공자
    
    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
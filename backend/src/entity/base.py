from sqlalchemy.orm import declarative_base
from src.database.mysql import engine

# 모델 생성을 위한 기본 클래스
Base = declarative_base()

def init_db():
    """
    테이블 생성을 위한 초기화 함수입니다.
    """
    from src import entity
    Base.metadata.create_all(bind=engine)
from sqlalchemy.orm import declarative_base
from src.database.mysql import engine

# 모델 생성을 위한 기본 클래스
Base = declarative_base()

def init_db():
    """
    테이블 생성을 위한 초기화 함수입니다.
    """
    from src.entity.category import Category
    from src.entity.citation_edge import CitationEdge
    from src.entity.feed import Feed
    from src.entity.paper_category import PaperCategory
    from src.entity.paper import Paper
    from src.entity.primary_category import PrimaryCategory
    from src.entity.summary import Summary
    from src.entity.user_event import UserEvent
    from src.entity.user_paper_category import UserPaperCategory
    from src.entity.user import User
    Base.metadata.create_all(bind=engine)

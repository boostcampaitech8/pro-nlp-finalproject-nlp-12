"""User Event Repository - 사용자 이벤트 데이터 접근 계층"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from src.entity.user_event import UserEvent
from src.repository.base import BaseRepository


class UserEventRepository(BaseRepository[UserEvent]):
    """사용자 이벤트 Repository"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserEvent)
    
    def get_by_user_id(
        self, 
        user_id: int,  # user_id는 integer FK
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[UserEvent]:
        """사용자 ID로 이벤트 조회"""
        stmt = (
            select(UserEvent)
            .where(UserEvent.user_id == user_id)
        )
        
        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        
        stmt = stmt.order_by(desc(UserEvent.created_at)).limit(limit)
        
        return self.db.execute(stmt).scalars().all()
    
    def get_by_user_and_paper(
        self, 
        user_id: int,  # user_id는 integer FK
        paper_id: int,
        event_type: Optional[str] = None
    ) -> List[UserEvent]:
        """사용자와 논문으로 이벤트 조회"""
        stmt = select(UserEvent).where(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id
            )
        )
        
        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        
        stmt = stmt.order_by(desc(UserEvent.created_at))
        
        return self.db.execute(stmt).scalars().all()
    
    def get_recent_events(
        self,
        user_id: int,  # user_id는 integer FK
        days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> List[UserEvent]:
        """최근 N일간의 이벤트 조회"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(UserEvent).where(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.created_at >= cutoff_date
            )
        )
        
        if event_types:
            stmt = stmt.where(UserEvent.event_type.in_(event_types))
        
        stmt = stmt.order_by(desc(UserEvent.created_at))
        
        return self.db.execute(stmt).scalars().all()
    
    def get_interacted_paper_ids(
        self,
        user_id: int,  # user_id는 integer FK
        event_types: Optional[List[str]] = None
    ) -> List[int]:
        """사용자가 상호작용한 논문 ID 목록"""
        stmt = select(UserEvent.paper_id.distinct()).where(
            UserEvent.user_id == user_id
        )
        
        if event_types:
            stmt = stmt.where(UserEvent.event_type.in_(event_types))
        
        return self.db.execute(stmt).scalars().all()
    
    def count_by_user(self, user_id: int, event_type: Optional[str] = None) -> int:
        """사용자의 이벤트 수"""
        stmt = select(func.count()).select_from(UserEvent).where(
            UserEvent.user_id == user_id
        )
        
        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        
        return self.db.execute(stmt).scalar()
    
    def exists_event(
        self,
        user_id: int,  # user_id는 integer FK
        paper_id: int,
        event_type: str
    ) -> bool:
        """특정 이벤트 존재 여부 확인"""
        stmt = select(func.count()).select_from(UserEvent).where(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type
            )
        )
        count = self.db.execute(stmt).scalar()
        return count > 0

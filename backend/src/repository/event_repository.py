"""Event Repository - 사용자 이벤트 접근 계층"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from src.entity.user_event import UserEvent, EventType
from src.repository.base import BaseRepository


class EventRepository(BaseRepository[UserEvent]):
    """사용자 이벤트 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, UserEvent)

    # ========== 조회 ==========

    def get_by_user(
        self,
        user_id: int,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[UserEvent]:
        """사용자의 이벤트 조회"""
        stmt = select(UserEvent).where(UserEvent.user_id == user_id)
        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        stmt = stmt.order_by(desc(UserEvent.created_at)).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def get_by_user_and_paper(
        self,
        user_id: int,
        paper_id: int,
        event_type: Optional[EventType] = None
    ) -> List[UserEvent]:
        """사용자 + 논문으로 이벤트 조회"""
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
        user_id: int,
        days: int = 30,
        event_types: Optional[List[EventType]] = None
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

    def get_recent_positive_events(self, user_id: int, limit: int = 100) -> List[UserEvent]:
        """최근 긍정 이벤트 조회 (like, bookmark, click)"""
        positive_types = [EventType.like, EventType.bookmark, EventType.click]
        stmt = (
            select(UserEvent)
            .where(UserEvent.user_id == user_id, UserEvent.event_type.in_(positive_types))
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_interacted_paper_ids(
        self,
        user_id: int,
        event_types: Optional[List[EventType]] = None
    ) -> List[int]:
        """사용자가 상호작용한 논문 ID 목록"""
        stmt = select(UserEvent.paper_id.distinct()).where(UserEvent.user_id == user_id)
        if event_types:
            stmt = stmt.where(UserEvent.event_type.in_(event_types))
        return self.db.execute(stmt).scalars().all()

    def get_seen_paper_ids(self, user_id: int, limit: int = 2000) -> set[int]:
        """이미 본 논문 ID (impression 기준)"""
        stmt = (
            select(UserEvent.paper_id)
            .where(
                UserEvent.user_id == user_id,
                UserEvent.event_type == EventType.impression,
            )
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        ids = self.db.execute(stmt).scalars().all()
        return set(ids)

    # ========== 존재 확인 ==========

    def exists_event(self, user_id: int, paper_id: int, event_type: EventType) -> bool:
        """특정 이벤트 존재 여부"""
        stmt = select(func.count()).select_from(UserEvent).where(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type
            )
        )
        return self.db.execute(stmt).scalar() > 0

    # ========== 생성/삭제 ==========

    def add_event(
        self,
        user_id: int,
        paper_id: int,
        event_type: EventType,
    ) -> UserEvent:
        """이벤트 추가"""
        event = UserEvent(
            user_id=user_id,
            paper_id=paper_id,
            event_type=event_type,
        )
        self.db.add(event)
        return event

    def delete_event(self, user_id: int, paper_id: int, event_type: EventType) -> int:
        """이벤트 삭제"""
        result = (
            self.db.query(UserEvent)
            .filter(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type,
            )
            .delete(synchronize_session=False)
        )
        return result

    def toggle_event(
        self,
        user_id: int,
        paper_id: int,
        event_type: EventType,
    ) -> bool:
        """이벤트 토글 (있으면 삭제, 없으면 추가). 반환: 활성 여부"""
        if self.exists_event(user_id, paper_id, event_type):
            self.delete_event(user_id, paper_id, event_type)
            return False
        self.add_event(user_id, paper_id, event_type)
        return True

    def upsert_click(self, user_id: int, paper_id: int) -> UserEvent:
        """클릭 이벤트 upsert (있으면 시간 갱신, 없으면 생성)"""
        stmt = select(UserEvent).where(
            and_(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == EventType.click
            )
        )
        event = self.db.execute(stmt).scalar_one_or_none()

        if event:
            event.created_at = datetime.utcnow()
        else:
            event = UserEvent(
                user_id=user_id,
                paper_id=paper_id,
                event_type=EventType.click,
            )
            self.db.add(event)

        self.db.commit()
        self.db.refresh(event)
        return event

    def count_by_user(self, user_id: int, event_type: Optional[EventType] = None) -> int:
        """사용자의 이벤트 수"""
        stmt = select(func.count()).select_from(UserEvent).where(UserEvent.user_id == user_id)
        if event_type:
            stmt = stmt.where(UserEvent.event_type == event_type)
        return self.db.execute(stmt).scalar()

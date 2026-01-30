from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.user_event import UserEvent


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    # (추가) 라우터(events.py)에서 호출하는 형태 지원
    def create(self, *, user_id: str, paper_id: int, event_type: str, weight: float) -> UserEvent:
        e = UserEvent(
            user_id=user_id,
            paper_id=paper_id,
            event_type=event_type,
            weight=weight,
        )
        self.db.add(e)  # commit은 라우터에서
        return e

    # 객체를 직접 추가하고 싶을 때(커밋은 라우터에서)
    def add_event(self, ev: UserEvent) -> None:
        self.db.add(ev)

    def get_recent_positive_events(self, user_id: str, limit: int = 100) -> list[UserEvent]:
        stmt = (
            select(UserEvent)
            .where(UserEvent.user_id == user_id, UserEvent.weight > 0)
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_seen_paper_ids(self, user_id: str, limit: int = 2000) -> set[int]:
        """
        '이미 본 것'은 impression 이벤트로만 판단한다.
        - 최신 impression부터 limit개까지의 paper_id를 반환
        """
        stmt = (
            select(UserEvent.paper_id)
            .where(
                UserEvent.user_id == user_id,
                UserEvent.event_type == "impression",
            )
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        ids = self.db.execute(stmt).scalars().all()
        return set(ids)


    def exists_event(self, *, user_id: str, paper_id: int, event_type: str) -> bool:
        q = (
            self.db.query(UserEvent)
            .filter(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type,
            )
            .first()
        )
        return q is not None

    def delete_event(self, *, user_id: str, paper_id: int, event_type: str) -> int:
        # 해당 타입 이벤트 전부 삭제 (중복이 이미 쌓였을 수 있으니까)
        n = (
            self.db.query(UserEvent)
            .filter(
                UserEvent.user_id == user_id,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type,
            )
            .delete(synchronize_session=False)
        )
        return n

    def toggle_event(self, *, user_id: str, paper_id: int, event_type: str, weight: float) -> bool:
        """
        return: active 여부
        - 없으면 insert -> True
        - 있으면 delete -> False
        """
        if self.exists_event(user_id=user_id, paper_id=paper_id, event_type=event_type):
            self.delete_event(user_id=user_id, paper_id=paper_id, event_type=event_type)
            return False

        e = UserEvent(
            user_id=user_id,
            paper_id=paper_id,
            event_type=event_type,
            weight=weight,
        )
        self.db.add(e)  # commit은 라우터에서
        return True

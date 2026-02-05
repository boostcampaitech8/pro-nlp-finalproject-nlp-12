from __future__ import annotations

import json
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from src.entity.user_event import UserEvent
from src.entity.user import User


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def _get_user_id(self, user_uuid: str) -> int | None:
        stmt = select(User).where(User.uuid == user_uuid)
        user = self.db.execute(stmt).scalars().first()
        return user.id if user else None

    def _ensure_user_id(self, user_uuid: str) -> int:
        stmt = select(User).where(User.uuid == user_uuid)
        user = self.db.execute(stmt).scalars().first()
        if user:
            return user.id

        user = User(
            uuid=user_uuid,
            user_vector_json=json.dumps([]),
            vector_dirty_at=None,
            has_onboarded=False,
            onboarding_json=None,
        )
        self.db.add(user)
        self.db.flush()
        return user.id

    # events.py에서 호출되는 형태 지원
    def create(self, *, user_id: str, paper_id: int, event_type: str) -> UserEvent:
        user_pk = self._ensure_user_id(user_id)
        e = UserEvent(
            user_id=user_pk,
            paper_id=paper_id,
            event_type=event_type,
        )
        self.db.add(e)  # commit은 caller
        return e

    # 객체를 직접 추가하고 락을 걸려면 호출
    def add_event(self, ev: UserEvent) -> None:
        self.db.add(ev)

    def get_recent_positive_events(self, user_id: str, limit: int = 100) -> list[UserEvent]:
        user_pk = self._get_user_id(user_id)
        if user_pk is None:
            return []
        stmt = (
            select(UserEvent)
            .where(
                UserEvent.user_id == user_pk,
                UserEvent.event_type.in_(["like", "bookmark", "click"]),
            )
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_seen_paper_ids(self, user_id: str, limit: int = 2000) -> set[int]:
        """
        '이미 본' 처리: impression 이벤트만 집계.
        - 최신 impression부터 limit까지 paper_id 반환
        """
        user_pk = self._get_user_id(user_id)
        if user_pk is None:
            return set()
        stmt = (
            select(UserEvent.paper_id)
            .where(
                UserEvent.user_id == user_pk,
                UserEvent.event_type == "impression",
            )
            .order_by(desc(UserEvent.created_at))
            .limit(limit)
        )
        ids = self.db.execute(stmt).scalars().all()
        return set(ids)

    def exists_event(self, *, user_id: str, paper_id: int, event_type: str) -> bool:
        user_pk = self._get_user_id(user_id)
        if user_pk is None:
            return False
        q = (
            self.db.query(UserEvent)
            .filter(
                UserEvent.user_id == user_pk,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type,
            )
            .first()
        )
        return q is not None

    def get_interacted_paper_ids(
        self,
        user_id: str,
        event_types: list[str] | None = None,
    ) -> list[int]:
        user_pk = self._get_user_id(user_id)
        if user_pk is None:
            return []
        q = self.db.query(UserEvent.paper_id).filter(UserEvent.user_id == user_pk)
        if event_types:
            q = q.filter(UserEvent.event_type.in_(event_types))
        rows = q.distinct().all()
        return [int(r[0]) for r in rows if r and r[0] is not None]

    def delete_event(self, *, user_id: str, paper_id: int, event_type: str) -> int:
        user_pk = self._get_user_id(user_id)
        if user_pk is None:
            return 0
        # 해당 유저 이벤트만 삭제 (중복 이벤트 없다고 가정)
        n = (
            self.db.query(UserEvent)
            .filter(
                UserEvent.user_id == user_pk,
                UserEvent.paper_id == paper_id,
                UserEvent.event_type == event_type,
            )
            .delete(synchronize_session=False)
        )
        return n

    def toggle_event(self, *, user_id: str, paper_id: int, event_type: str) -> bool:
        """
        return: active 여부
        - 없으면 insert -> True
        - 있으면 delete -> False
        """
        if self.exists_event(user_id=user_id, paper_id=paper_id, event_type=event_type):
            self.delete_event(user_id=user_id, paper_id=paper_id, event_type=event_type)
            return False

        user_pk = self._ensure_user_id(user_id)
        e = UserEvent(
            user_id=user_pk,
            paper_id=paper_id,
            event_type=event_type,
        )
        self.db.add(e)  # commit은 caller
        return True

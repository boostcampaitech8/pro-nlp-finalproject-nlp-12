from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.paper import Paper
from app.models.user_event import UserEvent


class LibraryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_library(
        self,
        *,
        user_id: str,
        event_type: str,  # "like" | "bookmark" | "all"
        limit: int,
        offset: int,
    ):
        # type 필터
        if event_type == "all":
            types = ["like", "bookmark"]
        else:
            types = [event_type]

        # (user_id, paper_id, event_type)별 최신 created_at 구하기
        latest_subq = (
            self.db.query(
                UserEvent.user_id.label("user_id"),
                UserEvent.paper_id.label("paper_id"),
                UserEvent.event_type.label("event_type"),
                func.max(UserEvent.created_at).label("max_created_at"),
            )
            .filter(
                UserEvent.user_id == user_id,
                UserEvent.event_type.in_(types),
            )
            .group_by(UserEvent.user_id, UserEvent.paper_id, UserEvent.event_type)
            .subquery()
        )

        # 최신 이벤트 row만 join해서 가져오기 + weight > 0 만 “활성”으로 간주
        base_q = (
            self.db.query(UserEvent, Paper)
            .join(
                latest_subq,
                and_(
                    UserEvent.user_id == latest_subq.c.user_id,
                    UserEvent.paper_id == latest_subq.c.paper_id,
                    UserEvent.event_type == latest_subq.c.event_type,
                    UserEvent.created_at == latest_subq.c.max_created_at,
                ),
            )
            .join(Paper, Paper.id == UserEvent.paper_id)
            .filter(UserEvent.weight > 0)
            .order_by(UserEvent.created_at.desc())
        )

        total = base_q.count()
        rows = base_q.offset(offset).limit(limit).all()

        items = []
        for ev, p in rows:
            items.append(
                {
                    "paper_id": p.id,
                    "event_type": ev.event_type,
                    "created_at": ev.created_at,
                    "title": getattr(p, "title", None),
                    "abstract": getattr(p, "abstract", None),
                    "authors": getattr(p, "authors", None),
                    "abs_url": getattr(p, "abs_url", None),
                    "pdf_url": getattr(p, "pdf_url", None),
                    "published_at": getattr(p, "published_at", None),
                }
            )

        return total, items

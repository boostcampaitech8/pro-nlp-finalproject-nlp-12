"""Library Repository - 라이브러리(좋아요/북마크 목록) 접근 계층"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.entity.paper import Paper
from src.entity.user_event import UserEvent, EventType


class LibraryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_library(
        self,
        user_id: int,
        event_type: str,  # "like" | "bookmark" | "all"
        limit: int,
        offset: int,
    ):
        """사용자의 라이브러리 목록 조회"""
        if event_type == "all":
            types = [EventType.like, EventType.bookmark]
        else:
            types = [EventType(event_type)]

        # 최신 이벤트 기준 서브쿼리
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

        # 최신 이벤트 + Paper 조인
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
            .order_by(UserEvent.created_at.desc())
        )

        total = base_q.count()
        rows = base_q.offset(offset).limit(limit).all()

        items = []
        for ev, p in rows:
            ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정 (abs_url 제거)
            items.append({
                "paper_id": p.id,
                "arxiv_id": p.arxiv_id,
                "event_type": ev.event_type.value,
                "created_at": ev.created_at,
                "title": p.title,
                "abstract": p.abstract,
                "pdf_url": p.pdf_url,
                "published_date": p.published_date,
            })

        return total, items

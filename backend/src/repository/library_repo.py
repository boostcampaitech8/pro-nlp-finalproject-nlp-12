from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from src.entity.paper import Paper
from src.entity.user_event import UserEvent
from src.entity.user import User
from src.entity.summary import Summary, SummaryType
from src.entity.primary_category import PrimaryCategory
from src.entity.paper_category import PaperCategory


def _to_datetime(dt: datetime | date | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, date):
        return datetime.combine(dt, time.min)
    return None


def _paper_fields(p: Paper) -> dict:
    arxiv_id = getattr(p, "arxiv_id", None)
    abs_url = getattr(p, "abs_url", None)
    if abs_url is None and arxiv_id:
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"

    published_at = _to_datetime(getattr(p, "published_at", None) or getattr(p, "published_date", None))

    primary_category = None
    pc = getattr(p, "primary_category", None)
    if pc is not None:
        cat = getattr(pc, "category", None)
        if cat is not None:
            primary_category = getattr(cat, "category_type", None)

    categories = None
    pcs = getattr(p, "paper_categories", None) or []
    cat_list = []
    for x in pcs:
        cat = getattr(x, "category", None)
        if cat is None:
            continue
        ct = getattr(cat, "category_type", None)
        if ct:
            cat_list.append(ct)
    if cat_list:
        categories = ", ".join(cat_list)

    summary = getattr(p, "summary", None)

    return {
        "title": getattr(p, "title", None),
        "abs_url": abs_url,
        "pdf_url": getattr(p, "pdf_url", None),
        "published_at": published_at,
        "primary_category": primary_category,
        "categories": categories,
        "summary": summary
    }


class LibraryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _get_user_id(self, user_uuid: str) -> int | None:
        user = self.db.query(User).filter(User.uuid == user_uuid).first()
        return user.id if user else None

    def list_library(
        self,
        *,
        user_id: str,
        event_type: str,  # "like" | "bookmark" | "all"
        limit: int,
        offset: int,
    ):
        user_pk = self._get_user_id(user_id)
        if user_pk is None:
            return 0, []

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
                UserEvent.user_id == user_pk,
                UserEvent.event_type.in_(types),
            )
            .group_by(UserEvent.user_id, UserEvent.paper_id, UserEvent.event_type)
            .subquery()
        )

        # 최신 이벤트 row만 join해서 가져오기
        base_q = (
            self.db.query(UserEvent, Paper, Summary.summary_text)
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
            .options(
                joinedload(Paper.primary_category).joinedload(PrimaryCategory.category),
                joinedload(Paper.paper_categories).joinedload(PaperCategory.category)
            )
            .outerjoin(
                Summary,
                and_(Paper.id==Summary.paper_id, Summary.summary_type==SummaryType.keypoint.value)
            )
            .order_by(UserEvent.created_at.desc())
        )

        total = base_q.count()
        rows = base_q.offset(offset).limit(limit).all()

        items = []
        for ev, p, summary in rows:
            setattr(p, "summary", summary)
            fields = _paper_fields(p)
            items.append(
                {
                    "paper_id": p.id,
                    "event_type": ev.event_type,
                    "created_at": ev.created_at,
                    **fields,
                }
            )

        return total, items

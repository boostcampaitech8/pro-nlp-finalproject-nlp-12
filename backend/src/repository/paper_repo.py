from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from src.entity.paper import Paper

class PaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, paper_id: int) -> Paper | None:
        stmt = select(Paper).where(Paper.id == paper_id)
        return self.db.execute(stmt).scalars().first()

    def get_by_ids(self, ids: list[int]) -> list[Paper]:
        if not ids:
            return []
        stmt = select(Paper).where(Paper.id.in_(ids))
        return self.db.execute(stmt).scalars().all()

    def fetch_batch(self, offset: int, limit: int) -> list[Paper]:
        stmt = select(Paper).order_by(Paper.id).offset(offset).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def get_recent_papers(self, limit: int = 100) -> list[Paper]:
        if hasattr(Paper, "published_date"):
            stmt = select(Paper).order_by(desc(getattr(Paper, "published_date"))).limit(limit)
        else:
            stmt = select(Paper).order_by(desc(getattr(Paper, "id"))).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def count_all(self) -> int:
        return self.db.query(Paper).count()

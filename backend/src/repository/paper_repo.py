from sqlalchemy.orm import Session
from sqlalchemy import select
from src.entity.paper import Paper

class PaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_ids(self, ids: list[int]) -> list[Paper]:
        if not ids:
            return []
        stmt = select(Paper).where(Paper.id.in_(ids))
        return self.db.execute(stmt).scalars().all()

    def fetch_batch(self, offset: int, limit: int) -> list[Paper]:
        stmt = select(Paper).order_by(Paper.id).offset(offset).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def count_all(self) -> int:
        return self.db.query(Paper).count()

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.mysql import get_mysql_db
from src.service.ingest_service import IngestService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/reindex_faiss_all")
def reindex_faiss_all(
    batch_size: int = 1000,
    start_offset: int = 0,
    db: Session = Depends(get_mysql_db),
):
    svc = IngestService(db)
    return svc.reindex_faiss_all(batch_size=batch_size, start_offset=start_offset)

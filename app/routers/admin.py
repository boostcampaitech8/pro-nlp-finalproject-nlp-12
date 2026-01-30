from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.ingest_service import IngestService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/sync_papers_to_chroma_all")
def sync_papers_to_chroma_all(
    batch_size: int = 1000,
    start_offset: int = 0,
    db: Session = Depends(get_db),
):
    svc = IngestService(db)

    offset = start_offset
    total_upserted = 0
    loops = 0

    while True:
        result = svc.sync_papers_to_chroma(offset=offset, limit=batch_size)
        batch_upserted = int(result.get("upserted", 0))

        loops += 1
        total_upserted += batch_upserted
        offset += batch_size

        # 더 이상 가져올 게 없으면 종료
        if batch_upserted == 0:
            break

    return {
        "ok": True,
        "batch_size": batch_size,
        "start_offset": start_offset,
        "loops": loops,
        "total_upserted": total_upserted,
        "final_offset": offset,
    }

from sqlalchemy.orm import Session

from src.repository.paper_repo import PaperRepository
from src.client.embedder import embed_texts
from src.client.faiss_store import get_faiss_store


class IngestService:
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.faiss = get_faiss_store()

    def sync_papers_to_faiss(self, offset: int = 0, limit: int = 1000) -> dict:
        papers = self.paper_repo.fetch_batch(offset=offset, limit=limit)
        if not papers:
            return {"added": 0, "offset": offset, "limit": limit}

        paper_ids = []
        docs = []

        for p in papers:
            pid = int(getattr(p, "id"))
            paper_ids.append(pid)

            text = (getattr(p, "title", "") or "").strip() + "\n\n" + (getattr(p, "abstract", "") or "").strip()
            docs.append(text)

        embeddings = embed_texts(docs)  # (n, dim)
        self.faiss.add_with_ids(paper_ids=paper_ids, vectors=embeddings)
        self.faiss.persist()

        return {"added": len(paper_ids), "offset": offset, "limit": limit}

    def reindex_faiss_all(self, batch_size: int = 1000, start_offset: int = 0) -> dict:
        """
        FAISS는 upsert가 번거로워서 MVP는 전체 재색인이 가장 안정적
        """
        self.faiss.reset()

        offset = start_offset
        total = 0
        loops = 0

        while True:
            out = self.sync_papers_to_faiss(offset=offset, limit=batch_size)
            added = int(out.get("added", 0))
            loops += 1
            total += added
            offset += batch_size
            if added == 0:
                break

        return {
            "ok": True,
            "batch_size": batch_size,
            "start_offset": start_offset,
            "loops": loops,
            "total_added": total,
            "final_offset": offset,
        }

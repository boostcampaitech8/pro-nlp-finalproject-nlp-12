from sqlalchemy.orm import Session
from app.repositories.paper_repo import PaperRepository
from app.core.chroma import get_collection
from app.core.embedder import embed_texts

class IngestService:
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)

    def sync_papers_to_chroma(self, offset: int = 0, limit: int = 1000) -> dict:
        col = get_collection()
        papers = self.paper_repo.fetch_batch(offset=offset, limit=limit)

        if not papers:
            return {"upserted": 0, "offset": offset, "limit": limit}

        ids = []
        docs = []
        metadatas = []

        for p in papers:
            doc_id = str(p.id)

            # 임베딩 텍스트 구성: title + abstract
            text = (p.title or "").strip() + "\n\n" + (p.abstract or "").strip()

            ids.append(doc_id)
            docs.append(text)
            metadatas.append({
                "paper_id": int(p.id),
                "arxiv_id": p.arxiv_id,
                "primary_category": p.primary_category,
                "published_at": str(p.published_at) if p.published_at else None,
            })

        embeddings = embed_texts(docs)

        col.upsert(
            ids=ids,
            documents=docs,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return {"upserted": len(ids), "offset": offset, "limit": limit}

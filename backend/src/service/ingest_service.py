"""논문 FAISS 인덱싱 서비스"""
from sqlalchemy.orm import Session

from src.repository.paper_repository import PaperRepository
from src.client.embedder import embed_texts
from src.client.faiss_store import get_faiss_store
from src.config.settings import settings


class IngestService:
    """논문을 FAISS 인덱스에 동기화하는 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.faiss = get_faiss_store(
            dim=settings.EMBEDDING_DIM,
            index_path=settings.FAISS_INDEX_PATH + "/index.bin"
        )

    def sync_papers_to_faiss(self, offset: int = 0, limit: int = 1000) -> dict:
        """
        DB 논문을 배치로 FAISS에 동기화

        Args:
            offset: 시작 위치
            limit: 배치 크기

        Returns:
            {"added": int, "offset": int, "limit": int}
        """
        papers = self.paper_repo.fetch_batch(offset=offset, limit=limit)
        if not papers:
            return {"added": 0, "offset": offset, "limit": limit}

        # 이미 인덱싱된 paper_id 제외
        existing_ids = self.faiss.get_existing_ids()

        paper_ids = []
        docs = []

        for p in papers:
            pid = int(p.id)
            if pid in existing_ids:
                continue

            paper_ids.append(pid)
            text = (p.title or "").strip() + "\n\n" + (p.abstract or "").strip()
            docs.append(text)

        if not paper_ids:
            return {"added": 0, "offset": offset, "limit": limit, "skipped": len(papers)}

        # 임베딩 생성 및 FAISS 추가
        embeddings = embed_texts(docs)
        self.faiss.add_with_ids(paper_ids=paper_ids, vectors=embeddings)
        self.faiss.persist()

        return {"added": len(paper_ids), "offset": offset, "limit": limit}

    def reindex_faiss_all(self, batch_size: int = 1000, start_offset: int = 0) -> dict:
        """
        FAISS 전체 재인덱싱

        Args:
            batch_size: 배치 크기
            start_offset: 시작 위치

        Returns:
            재인덱싱 결과
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

    def get_index_stats(self) -> dict:
        """인덱스 상태 조회"""
        return {
            "total_vectors": self.faiss.total_count,
            ### 수정사항: admin.py에서 dimension 접근하므로 추가
            "dimension": self.faiss.dim,
            "index_path": self.faiss.index_path,
        }

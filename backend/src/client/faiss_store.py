import os
import numpy as np
import faiss
# [추가] 임베딩을 위해 langchain_huggingface 추가
from langchain_huggingface import HuggingFaceEmbeddings
# [추가] Document type 표시를 위해 추가
from langchain_core.documents import Document

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms


class FaissStore:
    """
    - IndexFlatIP + IndexIDMap2
    - add_with_ids()로 paper_id를 그대로 FAISS id로 사용
    - search 결과 ids가 바로 paper_id
    - reconstruct(paper_id)로 해당 논문 임베딩을 다시 가져올 수 있음
    """

    def __init__(self, dim: int, index_path: str, model_name: str = "BAAI/bge-m3"):
        self.dim = int(dim)
        self.index_path = index_path
        self.index = self._load_or_create()

        # [추가] 임베딩 모델 로드
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},  # GPU가 있으면 'cuda'
            encode_kwargs={"normalize_embeddings": True}
        )

    def _create_empty(self):
        base = faiss.IndexFlatIP(self.dim)
        return faiss.IndexIDMap2(base)

    def _load_or_create(self):
        if os.path.exists(self.index_path):
            idx = faiss.read_index(self.index_path)
            return idx
        return self._create_empty()

    def persist(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)

    def reset(self):
        self.index = self._create_empty()
        self.persist()

    def add_with_ids(self, paper_ids: list[int], vectors: np.ndarray):
        """
        vectors: (n, dim) float32/float64
        paper_ids: list[int]
        """
        if vectors is None or len(paper_ids) == 0:
            return

        v = np.asarray(vectors, dtype="float32")
        if v.ndim != 2 or v.shape[1] != self.dim:
            raise ValueError(f"vectors shape mismatch: got {v.shape}, expected (*, {self.dim})")

        ids = np.asarray(paper_ids, dtype="int64")
        if ids.ndim != 1:
            raise ValueError("paper_ids must be 1D")

        v = _l2_normalize(v)
        self.index.add_with_ids(v, ids)

    # [추가]
    def update_papers(self, papers: list[Document]):
        """
        논문 리스트를 받아, 새로운 논문만 인덱스에 추가합니다.
        """
        # 현재 인덱스에 있는 모든 ID
        existing_ids = self.get_existing_ids()

        # 신규 논문만 필터링
        new_papers = [p for p in papers if p.metadata["paper_id"] not in existing_ids]

        if not new_papers:
            return
        
        # 임베딩할 텍스트 추출
        texts = [f"Title: {p.metadata['title']}\n\nAbstract: {p.metadata['abstract']}" for p in new_papers]
        new_paper_ids = [p.metadata["paper_id"] for p in new_papers]

        # 임베딩 생성
        vectors = self.embeddings.embed_documents(texts)
        vectors = np.array(vectors, dtype="float32")

        # FAISS에 추가 및 저장
        self.add_with_ids(new_paper_ids, vectors)
        self.persist()

    def search(self, query_vec: np.ndarray, k: int):
        """
        return: (scores, paper_ids) both 1D
        scores = cosine similarity (normalize + IP)
        """
        q = np.asarray(query_vec, dtype="float32").reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError(f"query dim mismatch: got {q.shape[1]}, expected {self.dim}")

        q = _l2_normalize(q)
        scores, ids = self.index.search(q, int(k))
        return scores[0], ids[0]

    # [추가] 사용자 질의 기반 논문 추천을 위한 search() 메서드
    def search_by_query_str(self, query: str, k: int):
        """
        return: (scores, paper_ids) both 1D
        scores = cosine similarity (normalize + IP)
        """
        # [추가] query -> query_vec 임베딩 로직
        query_vec = self.embeddings.embed_query(query)
        query_vec = np.array(query_vec)

        q = np.asarray(query_vec, dtype="float32").reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError(f"query dim mismatch: got {q.shape[1]}, expected {self.dim}")

        q = _l2_normalize(q)
        scores, ids = self.index.search(q, int(k))
        return scores[0], ids[0]

    def reconstruct(self, paper_id: int) -> np.ndarray:
        """
        paper_id로 임베딩 벡터를 다시 꺼냄(인덱스에 있어야 함)
        """
        v = np.zeros((self.dim,), dtype="float32")
        self.index.reconstruct(int(paper_id), v)
        return v
    
    def get_existing_ids(self) -> set[int]:
        """
        인덱스에 저장된 모든 paper_id 반환 (중복 방지용)
        """
        if self.index.ntotal == 0:
            return set()
        ids = faiss.vector_to_array(self.index.id_map)
        return set(ids.tolist())

    def get_vectors_by_ids(self, paper_ids: list[int]) -> dict[int, np.ndarray]:
        """
        여러 paper_id로 벡터 한번에 조회 (유저 벡터 계산 시 사용)

        Args:
            paper_ids: 조회할 paper_id 리스트

        Returns:
            dict[int, np.ndarray]: paper_id -> 벡터 매핑
        """
        existing = self.get_existing_ids()
        result = {}
        for pid in paper_ids:
            if pid in existing:
                result[pid] = self.reconstruct(pid)
        return result

    @property
    def total_count(self) -> int:
        """인덱스 내 총 벡터 수"""
        return self.index.ntotal


# 싱글톤 getter (원하면 DI로 바꿔도 됨)
_STORE = None

def get_faiss_store(dim: int, index_path: str) -> FaissStore:
    global _STORE
    if _STORE is None:
        _STORE = FaissStore(dim=dim, index_path=index_path)
    return _STORE
import os
import numpy as np
import faiss


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

    def __init__(self, dim: int, index_path: str):
        self.dim = int(dim)
        self.index_path = index_path
        self.index = self._load_or_create()

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

    def reconstruct(self, paper_id: int) -> np.ndarray:
        """
        paper_id로 임베딩 벡터를 다시 꺼냄(인덱스에 있어야 함)
        """
        v = np.zeros((self.dim,), dtype="float32")
        self.index.reconstruct(int(paper_id), v)
        return v


# 싱글톤 getter (원하면 DI로 바꿔도 됨)
_STORE = None

def get_faiss_store(dim: int, index_path: str) -> FaissStore:
    global _STORE
    if _STORE is None:
        _STORE = FaissStore(dim=dim, index_path=index_path)
    return _STORE

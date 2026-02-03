"""FAISS 인덱싱 및 검색 서비스"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from src.config.settings import settings
# [추가] 임베딩을 위해 langchain_huggingface 추가
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class FAISSService:
    """FAISS 벡터 인덱스 관리 (싱글톤 + 메모리 캐싱)"""

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_path / "paper_index.faiss"
        self.metadata_file = self.index_path / "metadata.json"

        # [추가] 임베딩 모델 로드
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},  # GPU가 있으면 'cuda'
            encode_kwargs={"normalize_embeddings": True}
        )

        ### 수정사항: 메모리 캐싱을 위한 인스턴스 변수 추가
        self._index = None  # FAISS index 객체 캐시
        self._id_map = None  # 메타데이터 캐시

    def save_index(self, index, metadata: dict):
        """FAISS 인덱스를 파일로 저장 + 캐시 업데이트"""
        try:
            import faiss
            faiss.write_index(index, str(self.index_file))

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            ### 수정사항: 저장 후 캐시 업데이트
            self._index = index
            self._id_map = metadata

            logger.info(f"Saved FAISS index with {index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
            return False

    def load_index(self):
        """저장된 FAISS 인덱스 로드 (캐시 우선)"""
        try:
            import faiss

            ### 수정사항: 캐시에 있으면 바로 반환 (디스크 I/O 생략)
            if self._index is not None:
                return self._index, self._id_map

            if not self.index_file.exists():
                logger.info("Creating new FAISS index")
                self._index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
                self._id_map = {}
                return self._index, self._id_map

            logger.info(f"Loading FAISS index from {self.index_file}")
            self._index = faiss.read_index(str(self.index_file))

            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self._id_map = json.load(f)

            logger.info(f"Loaded {self._index.ntotal} vectors")
            return self._index, self._id_map
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return None, None

    def search(self, query_vector: np.ndarray, k: int = 10):
        """
        벡터 유사도 검색

        Args:
            query_vector: (EMBEDDING_DIM,) 형태의 검색 쿼리
            k: 반환할 결과 수

        Returns:
            list[dict]: 검색 결과 (score, paper_id, metadata 포함)
        """
        index, id_map = self.load_index()
        if index is None or index.ntotal == 0:
            return []

        # 배치 형태로 변환
        query = query_vector.reshape(1, -1).astype(np.float32)
        distances, indices = index.search(query, min(k, index.ntotal))

        ### 수정사항: mvp2처럼 풍부한 결과 반환
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:  # FAISS returns -1 for not found
                continue
            meta = id_map.get(str(idx), {})
            results.append({
                "faiss_id": int(idx),
                "score": float(dist),
                **meta,
            })

        return results

    def add_papers(self, paper_ids: list[int], embeddings: np.ndarray, metadatas: list[dict] = None):
        """
        논문 벡터를 인덱스에 추가

        Args:
            paper_ids: 논문 ID 리스트
            embeddings: (N, EMBEDDING_DIM) 형태의 임베딩 배열
            metadatas: 각 논문의 메타데이터 (optional)
        """
        try:
            import faiss

            index, id_map = self.load_index()

            # 인덱스가 없으면 새로 생성
            if index is None:
                index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
                id_map = {}

            # 현재 인덱스 크기 = 다음 faiss_id 시작점
            start_id = index.ntotal

            # 벡터 추가
            embeddings = np.array(embeddings, dtype=np.float32)
            index.add(embeddings)

            # 메타데이터 매핑
            for i, paper_id in enumerate(paper_ids):
                faiss_id = start_id + i
                meta = metadatas[i] if metadatas else {}
                id_map[str(faiss_id)] = {
                    "paper_id": paper_id,
                    **meta,
                }

            # 저장 (캐시도 자동 업데이트됨)
            self.save_index(index, id_map)
            logger.info(f"Added {len(paper_ids)} papers to FAISS index (total: {index.ntotal})")
            return True

        except Exception as e:
            logger.error(f"Error adding papers to FAISS: {e}")
            return False
    
    # [추가] 신규 논문만 인덱스에 추가하는 메서드
    def update_papers(self, all_papers: list) -> None:
        """
        신규 논문 벡터를 인덱스에 추가
        """
        existing_ids = self.get_existing_paper_ids()

        # 신규 데이터만 필터링
        new_docs = [doc for doc in all_papers if doc.metadata.get("paper_id") not in existing_ids]

        if new_docs:
            texts = [doc.page_content for doc in new_docs]
            paper_ids = [doc.metadata.get("paper_id") for doc in new_docs]
            metadatas = [doc.metadata for doc in new_docs]

            vectors = self.embeddings.embed_documents(texts)

            self.add_papers(
                paper_ids=paper_ids,
                embeddings=np.array(vectors),
                metadatas=metadatas
            )

    def get_existing_paper_ids(self) -> set[int]:
        """이미 인덱싱된 paper_id 집합 반환 (중복 방지용)"""
        _, id_map = self.load_index()
        if id_map is None:
            return set()
        return {meta.get("paper_id") for meta in id_map.values() if meta.get("paper_id")}

    def clear_index(self):
        """인덱스 초기화 (모든 벡터 삭제) - 개발/디버깅용"""
        try:
            import faiss

            ### 수정사항: 캐시도 함께 초기화
            self._index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
            self._id_map = {}
            self.save_index(self._index, self._id_map)
            logger.info("FAISS index cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing FAISS index: {e}")
            return False

    def get_total_count(self) -> int:
        """인덱스 내 총 벡터 수"""
        index, _ = self.load_index()
        if index is None:
            return 0
        return index.ntotal

    ### 수정사항: mvp2에서 가져온 get_vectors_by_paper_ids 함수 추가
    def get_vectors_by_paper_ids(self, paper_ids: list[int]) -> dict[int, np.ndarray]:
        """
        paper_id로 벡터 조회 (유저 벡터 계산 시 사용)

        Args:
            paper_ids: 조회할 논문 ID 리스트

        Returns:
            dict[int, np.ndarray]: paper_id -> 벡터 매핑
        """
        index, id_map = self.load_index()
        if index is None:
            return {}

        # paper_id -> faiss_id 매핑 생성
        paper_to_faiss = {}
        for faiss_id, meta in id_map.items():
            pid = meta.get("paper_id")
            if pid in paper_ids:
                paper_to_faiss[pid] = int(faiss_id)

        # 벡터 조회
        result = {}
        for paper_id, faiss_id in paper_to_faiss.items():
            vec = index.reconstruct(faiss_id)
            result[paper_id] = vec

        return result


# 싱글톤 인스턴스
faiss_service = FAISSService()
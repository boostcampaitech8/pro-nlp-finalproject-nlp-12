"""FAISS 인덱싱 및 검색 서비스"""
import os
import json
import numpy as np
from pathlib import Path
from src.config.settings import settings


class FAISSService:
    """FAISS 벡터 인덱스 관리"""
    
    def __init__(self):
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_path / "paper_index.faiss"
        self.metadata_file = self.index_path / "metadata.json"
        
    def save_index(self, index, metadata: dict):
        """FAISS 인덱스를 파일로 저장"""
        try:
            import faiss
            faiss.write_index(index, str(self.index_file))
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
            return False
    
    def load_index(self):
        """저장된 FAISS 인덱스 로드"""
        try:
            import faiss
            
            if not self.index_file.exists():
                return None, None
            
            index = faiss.read_index(str(self.index_file))
            
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return index, metadata
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            return None, None
    
    def search(self, query_vector: np.ndarray, k: int = 10):
        """
        벡터 유사도 검색
        
        Args:
            query_vector: (EMBEDDING_DIM,) 형태의 검색 쿼리
            k: 반환할 결과 수
            
        Returns:
            distances, indices: 거리와 인덱스 배열
        """
        try:
            import faiss
            
            index, metadata = self.load_index()
            if index is None:
                return [], []
            
            # 배치 형태로 변환
            query = np.array([query_vector], dtype=np.float32)
            distances, indices = index.search(query, k)
            
            return distances[0].tolist(), indices[0].tolist()
        except Exception as e:
            print(f"Error searching FAISS index: {e}")
            return [], []


# 싱글톤 인스턴스
faiss_service = FAISSService()

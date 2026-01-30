"""Paper Repository - 논문 데이터 접근 계층"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc

from src.entity.paper import Paper
from src.repository.base import BaseRepository


class PaperRepository(BaseRepository[Paper]):
    """논문 데이터 Repository"""
    
    def __init__(self, db: Session):
        super().__init__(db, Paper)
    
    def get_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        """ArXiv ID로 논문 조회"""
        stmt = select(Paper).where(Paper.arxiv_id == arxiv_id)
        return self.db.execute(stmt).scalars().first()
    
    def get_by_ids(self, paper_ids: List[int]) -> List[Paper]:
        """여러 ID로 논문 조회"""
        stmt = select(Paper).where(Paper.id.in_(paper_ids))
        return self.db.execute(stmt).scalars().all()
    
    def get_by_arxiv_ids(self, arxiv_ids: List[str]) -> List[Paper]:
        """여러 ArXiv ID로 논문 조회"""
        stmt = select(Paper).where(Paper.arxiv_id.in_(arxiv_ids))
        return self.db.execute(stmt).scalars().all()
    
    def search_by_title(self, keyword: str, limit: int = 20) -> List[Paper]:
        """제목으로 논문 검색"""
        stmt = (
            select(Paper)
            .where(Paper.title.like(f"%{keyword}%"))
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()
    
    def get_by_categories(self, categories: List[str], limit: int = 50) -> List[Paper]:
        """카테고리로 논문 조회 (primary_category 기준)"""
        # 새 엔티티에는 primary_category 없으므로 전체 논문 반환
        stmt = (
            select(Paper)
            .order_by(desc(Paper.citation_count))
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()
    
    def get_by_categories_with_citations(
        self, 
        categories: List[str], 
        min_citations: int = 1,
        limit: int = 50
    ) -> List[Paper]:
        """카테고리 및 인용수 조건으로 논문 조회"""
        # 새 엔티티에는 primary_category 없으므로 인용수만 필터링
        stmt = (
            select(Paper)
            .where(Paper.citation_count >= min_citations)
            .order_by(desc(Paper.citation_count))
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()
    
    def get_recent_papers(self, limit: int = 100) -> List[Paper]:
        """최신 논문 조회"""
        stmt = (
            select(Paper)
            .order_by(Paper.published_date.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()
    
    def exists_by_arxiv_id(self, arxiv_id: str) -> bool:
        """ArXiv ID 존재 여부 확인"""
        stmt = select(func.count()).select_from(Paper).where(Paper.arxiv_id == arxiv_id)
        count = self.db.execute(stmt).scalar()
        return count > 0
    
    def count_all(self) -> int:
        """전체 논문 수"""
        stmt = select(func.count()).select_from(Paper)
        return self.db.execute(stmt).scalar()

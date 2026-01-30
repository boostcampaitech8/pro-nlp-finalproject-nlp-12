"""Base Repository - 모든 Repository의 기본 클래스"""
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    기본 Repository 클래스
    
    모든 Repository가 상속받아 공통 CRUD 기능 제공
    """
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """ID로 단일 레코드 조회"""
        return self.db.get(self.model, id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """전체 레코드 조회 (페이징)"""
        stmt = select(self.model).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()
    
    def create(self, entity: T) -> T:
        """새 레코드 생성"""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, entity: T) -> T:
        """레코드 업데이트"""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity: T) -> None:
        """레코드 삭제"""
        self.db.delete(entity)
        self.db.commit()
    
    def bulk_create(self, entities: List[T]) -> List[T]:
        """여러 레코드 한번에 생성"""
        self.db.add_all(entities)
        self.db.commit()
        for entity in entities:
            self.db.refresh(entity)
        return entities

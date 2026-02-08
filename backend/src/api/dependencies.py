from fastapi import Request, Depends
from sqlalchemy.orm import Session
from src.database.mysql import get_mysql_db
from src.database.valkey import get_valkey_db
from src.service.paper_service import PaperService
from typing import List
from redis import asyncio

# 서비스 인스턴스를 관리하는 함수(의존성 주입용)
def get_paper_service(
    request: Request,
    db: Session = Depends(get_mysql_db),
    valkey: asyncio.Redis = Depends(get_valkey_db)
) -> PaperService:
    search_service = request.app.state.search_service
    return PaperService(db, search_service, valkey)
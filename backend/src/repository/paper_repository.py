from src.database.mysql import get_mysql_db
from typing import List, Dict

class PaperRepository:
    @staticmethod
    def get_liked_papers_by_session_id(session_id: str) -> List[Dict]:
        """
        사용자가 '좋아요'한 모든 논문을 반환합니다.
        """
        with get_mysql_db() as db:
            with db.cursor() as cursor:
                sql = """
                SELECT p.arxiv_id, p.title, p.abstract
                FROM papers p
                JOIN likes l ON p.id = l.paper_id
                JOIN users u ON u.id = l.user_id
                WHERE u.session_id = %s
                ORDER BY l.created_at DESC  -- 최근에 좋아요를 누른 순서대로 정렬
                """
                cursor.execute(sql, (session_id,))
                paper_res = cursor.fetchall()

                return paper_res if paper_res else []

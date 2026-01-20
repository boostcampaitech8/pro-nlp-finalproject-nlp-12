from src.database.mysql import get_mysql_db

class LikeRepository:
    @staticmethod
    def toggle(session_id: str, arxiv_id: str) -> bool:
        """
        좋아요 상태를 토글합니다.
        - 데이터가 없으면 INSERT (True 반환)
        - 데이터가 있으면 DELETE (False 반환)
        """
        with get_mysql_db() as db:
            with db.cursor() as cursor:
                # --- 좋아요 존재 여부 확인 ---
                find_sql = """
                SELECT 
                u.id AS user_id, 
                p.id AS paper_id, 
                (l.user_id IS NOT NULL) AS is_liked
                FROM users u
                CROSS JOIN papers p
                LEFT JOIN likes l ON l.user_id = u.id AND l.paper_id = p.id
                WHERE u.session_id = %s AND p.arxiv_id = %s
                """
                
                cursor.execute(find_sql, (session_id, arxiv_id))
                like_res = cursor.fetchone()

                is_liked = like_res["is_liked"]
                user_id = like_res["user_id"]
                paper_id = like_res["paper_id"]

                if is_liked:
                    # --- 좋아요 취소 ---
                    cursor.execute("DELETE FROM likes WHERE user_id = %s AND paper_id = %s", (user_id, paper_id))
                    new_state = False
                else:
                    # --- 좋아요 추가 ---
                    cursor.execute("INSERT INTO likes (user_id, paper_id) VALUES (%s, %s)", (user_id, paper_id))
                    new_state = True

                db.commit()
                return new_state
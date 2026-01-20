from src.database.mysql import get_mysql_db

class UserRepository:
    @staticmethod
    def save(session_id: str) -> None:
        """
        session_id를 저장합니다.
        """
        with get_mysql_db() as db:
            with db.cursor() as cursor:
                sql = "INSERT INTO users (session_id) VALUES (%s)"
                cursor.execute(sql, (session_id,))
                db.commit()
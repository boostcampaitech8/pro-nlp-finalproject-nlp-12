import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def main():
    load_dotenv()

    DATABASE_URL = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
        f"?charset={os.getenv('DB_CHARSET', 'utf8mb4')}"
    )

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with engine.connect() as conn:
        # ✅ v5로 고정
        conn.execute(text("USE `papers_v5`;"))
        print("Current DB:", conn.execute(text("SELECT DATABASE();")).scalar())

        def show_columns(table: str):
            rows = conn.execute(text(f"SHOW COLUMNS FROM `{table}`;")).fetchall()
            print(f"\n=== COLUMNS: {table} ===")
            for r in rows:
                # (Field, Type, Null, Key, Default, Extra)
                print(r)

        def preview_rows(table: str, limit: int = 10):
            rows = conn.execute(text(f"SELECT * FROM `{table}` LIMIT {limit};")).fetchall()
            print(f"\n=== PREVIEW: {table} (LIMIT {limit}) ===")
            if not rows:
                print("(no rows)")
                return
            for r in rows:
                print(r)

        def count_rows(table: str):
            n = conn.execute(text(f"SELECT COUNT(*) FROM `{table}`;")).scalar()
            print(f"\n=== COUNT: {table} ===")
            print(n)

        # 1) 스키마 확인
        for t in ["users", "user_events"]:
            show_columns(t)

        # 2) 전체 row 수
        for t in ["users", "user_events"]:
            count_rows(t)

        # 3) 샘플 데이터(최근 것 보고 싶으면 아래 ORDER BY 컬럼을 조정해야 함)
        #    created_at 같은 컬럼이 있으면 그걸로 정렬 시도
        def preview_recent(table: str, limit: int = 20):
            # created_at / updated_at / id 후보 중 존재하는 걸 찾아서 정렬
            cols = [r[0] for r in conn.execute(text(f"SHOW COLUMNS FROM `{table}`;")).fetchall()]
            order_candidates = ["created_at", "updated_at", "event_time", "timestamp", "id"]
            order_col = next((c for c in order_candidates if c in cols), None)

            if order_col:
                rows = conn.execute(
                    text(f"SELECT * FROM `{table}` ORDER BY `{order_col}` DESC LIMIT {limit};")
                ).fetchall()
                print(f"\n=== RECENT: {table} (ORDER BY {order_col} DESC, LIMIT {limit}) ===")
            else:
                rows = conn.execute(text(f"SELECT * FROM `{table}` LIMIT {limit};")).fetchall()
                print(f"\n=== RECENT: {table} (no obvious time/id column; fallback LIMIT {limit}) ===")

            if not rows:
                print("(no rows)")
                return
            for r in rows:
                print(r)

        preview_recent("users", limit=20)
        preview_recent("user_events", limit=50)

        # 4) user_events 이벤트 타입별 카운트 (event_type 컬럼이 있을 때만)
        event_cols = [r[0] for r in conn.execute(text("SHOW COLUMNS FROM `user_events`;")).fetchall()]
        if "event_type" in event_cols:
            rows = conn.execute(
                text("SELECT event_type, COUNT(*) AS cnt FROM `user_events` GROUP BY event_type ORDER BY cnt DESC;")
            ).fetchall()
            print("\n=== user_events by event_type ===")
            for r in rows:
                print(r)
        else:
            print("\n(user_events에 event_type 컬럼이 없어 이벤트 타입 집계는 스킵)")

if __name__ == "__main__":
    main()

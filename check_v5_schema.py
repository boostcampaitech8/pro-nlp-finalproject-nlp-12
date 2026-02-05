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
        conn.execute(text("USE `papers_v5`;"))

        current_db = conn.execute(text("SELECT DATABASE();")).scalar()
        print(f"\n=== Current DB: {current_db} ===")

        tables = conn.execute(text("SHOW TABLES;")).fetchall()

        print("\n=== TABLE LIST ===")
        for (table_name,) in tables:
            print(f"- {table_name}")

        print("\n=== TABLE SCHEMA DETAIL ===")
        for (table_name,) in tables:
            print(f"\n--- {table_name} ---")
            columns = conn.execute(
                text(f"SHOW COLUMNS FROM `{table_name}`;")
            ).fetchall()
            for col in columns:
                print(col)

if __name__ == "__main__":
    main()

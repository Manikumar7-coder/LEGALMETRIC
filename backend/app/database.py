import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safemetric.db")

connect_args = {"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_database_schema(bind_engine=None):
    """
    Idempotent schema synchronization helper for SQLite.
    Ensures that any new columns added to models (e.g. inspection_id, ocr_info, rule_results)
    are properly migrated into the existing SQLite database without data loss.
    """
    eng = bind_engine or engine
    try:
        from sqlalchemy import text
        with eng.connect() as conn:
            # Check if inspections table exists
            check_table = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='inspections'")).fetchone()
            if check_table:
                res = conn.execute(text("PRAGMA table_info(inspections)"))
                existing_cols = {row[1] for row in res.fetchall()}
                
                if "inspection_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN inspection_id VARCHAR(100)"))
                if "ocr_info" not in existing_cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN ocr_info JSON"))
                if "rule_results" not in existing_cols:
                    conn.execute(text("ALTER TABLE inspections ADD COLUMN rule_results JSON"))
                conn.commit()
    except Exception as e:
        # Silently log or ignore if database is in memory or not sqlite
        print(f"[Schema Sync Notice] {e}")

def get_db():
    ensure_database_schema()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


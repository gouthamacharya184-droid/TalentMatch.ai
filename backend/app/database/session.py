import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Configure engine based on SQLite or PostgreSQL
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    # Normalize relative sqlite path to canonical backend directory
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        rel_path = db_url.replace("sqlite:///", "")
        if rel_path.startswith("./") or not os.path.isabs(rel_path):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            abs_db_file = os.path.normpath(os.path.join(base_dir, rel_path.lstrip("./")))
            db_url = f"sqlite:///{abs_db_file}"

    engine = create_engine(
        db_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 60,
        },
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.close()
else:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides an active database session."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

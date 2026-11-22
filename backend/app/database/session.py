import os
import shutil
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure engine based on SQLite or PostgreSQL
db_url = settings.DATABASE_URL

# Fix legacy or cloud-provider postgres:// schema prefix (e.g., Neon / Supabase / Render)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

is_vercel = bool(os.environ.get("VERCEL"))

if db_url.startswith("sqlite"):
    # If running in Vercel serverless with SQLite, ensure DB is writable by copying to /tmp
    if is_vercel:
        tmp_db_path = "/tmp/talentmatch.db"
        if not os.path.exists(tmp_db_path):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            root_dir = os.path.abspath(os.path.join(base_dir, ".."))
            for candidate in (os.path.join(base_dir, "talentmatch.db"), os.path.join(root_dir, "talentmatch.db")):
                if os.path.exists(candidate):
                    try:
                        shutil.copy2(candidate, tmp_db_path)
                        logger.info(f"Copied seeded SQLite database to {tmp_db_path} for serverless execution.")
                        break
                    except Exception as e:
                        logger.warning(f"Could not copy SQLite database to /tmp: {e}")
        db_url = f"sqlite:///{tmp_db_path}"
    else:
        # Normalize relative sqlite path to canonical backend directory in local dev
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
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.close()
        except Exception:
            pass
else:
    # Production PostgreSQL connection
    # In serverless environments, NullPool avoids accumulating stale idle connections
    if is_vercel:
        engine = create_engine(
            db_url,
            poolclass=NullPool,
            pool_pre_ping=True,
            echo=False,
        )
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

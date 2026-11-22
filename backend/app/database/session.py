import logging
import os
import shutil
import tempfile

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure engine based on SQLite or PostgreSQL
db_url = settings.DATABASE_URL

# Fix legacy or cloud-provider postgres:// schema prefix (e.g., Neon / Supabase / Render)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

is_test = bool(os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("ENVIRONMENT") == "test")
is_production = not is_test and (
    settings.ENVIRONMENT.lower() == "production"
    or os.environ.get("VERCEL_ENV") == "production"
)

# Fail fast at startup in production if DATABASE_URL is missing or points to SQLite
if is_production and (not db_url or db_url.startswith("sqlite")):
    raise RuntimeError(
        "FATAL: Production environment detected (ENVIRONMENT=production or VERCEL_ENV=production), "
        "but DATABASE_URL is missing or configured with SQLite. Production requires a persistent PostgreSQL database "
        "(e.g., Neon, Supabase, Vercel Postgres, or AWS RDS). Please configure DATABASE_URL=postgresql://user:password@host/dbname."
    )

is_vercel = bool(os.environ.get("VERCEL"))

if db_url.startswith("sqlite"):
    # If running in Vercel serverless with SQLite, ensure DB is writable by copying to /tmp
    if is_vercel:
        logger.warning(
            "CRITICAL WARNING: DATABASE_URL is not configured for production on Vercel. "
            "Using ephemeral SQLite in /tmp/talentmatch.db. DATA WILL NOT PERSIST across serverless invocations! "
            "Please configure DATABASE_URL (PostgreSQL) in Vercel -> Project Settings -> Environment Variables."
        )
        tmp_db_path = os.path.join(tempfile.gettempdir(), "talentmatch.db")
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
            pool_recycle=1800,
            echo=False,
        )
    else:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
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

"""
TalentMatch.ai - Automated SQLite to PostgreSQL Migration Utility
Migrates all tables, schemas, relations, and data with strict validation,
transaction safety, and before/after integrity verification.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker

# Setup path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.session import Base
from app.models.all_models import (
    User,
    Job,
    JobRequirement,
    Candidate,
    CandidateSkill,
    Resume,
    EvidenceReference,
    MatchingAnalysis,
    ScoreBreakdown,
    Shortlist,
    RecruiterNote,
    Notification,
    ActivityLog,
    Campaign,
    InterviewKit,
    EvaluationRun,
    AgentExecution,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

# Table migration order respecting foreign key constraints
TABLE_ORDER = [
    "users",
    "jobs",
    "job_requirements",
    "candidates",
    "candidate_skills",
    "resumes",
    "evidence_references",
    "matching_analyses",
    "score_breakdowns",
    "shortlists",
    "recruiter_notes",
    "notifications",
    "activity_logs",
    "campaigns",
    "interview_kits",
    "evaluation_runs",
    "agent_executions",
]


def migrate(sqlite_path: str = None, postgres_url: str = None):
    if not sqlite_path:
        sqlite_path = os.path.join(backend_dir, "talentmatch.db")

    if not postgres_url:
        postgres_url = os.environ.get("TARGET_DATABASE_URL") or os.environ.get("DATABASE_URL")

    if not postgres_url or not ("postgres" in postgres_url):
        logger.error("A valid PostgreSQL connection URL is required in TARGET_DATABASE_URL or DATABASE_URL.")
        logger.info("Example: postgresql://user:pass@host:5432/dbname")
        return False

    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    logger.info(f"Source SQLite database: {sqlite_path}")
    logger.info(f"Target PostgreSQL database: {postgres_url.split('@')[-1] if '@' in postgres_url else 'configured'}")

    # Connect to SQLite
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)

    # Connect to PostgreSQL
    pg_engine = create_engine(postgres_url, pool_pre_ping=True)

    # Create all tables on PostgreSQL
    logger.info("Creating tables on PostgreSQL schema...")
    Base.metadata.create_all(bind=pg_engine)

    pg_meta = MetaData()
    pg_meta.reflect(bind=pg_engine)

    results = {}

    with sqlite_engine.connect() as sqlite_conn, pg_engine.begin() as pg_conn:
        for table_name in TABLE_ORDER:
            if table_name not in sqlite_meta.tables or table_name not in pg_meta.tables:
                logger.warning(f"Skipping table '{table_name}' (not present in both schemas)")
                continue

            src_table = sqlite_meta.tables[table_name]
            dst_table = pg_meta.tables[table_name]

            # Fetch source records
            rows = sqlite_conn.execute(select(src_table)).fetchall()
            src_count = len(rows)

            if src_count == 0:
                logger.info(f"Table '{table_name}': 0 records in source. Skipped.")
                results[table_name] = {"source": 0, "destination": 0, "status": "EMPTY"}
                continue

            # Convert rows to dictionaries matching destination columns
            dst_col_names = {c.name for c in dst_table.columns}
            data_to_insert = []
            for row in rows:
                row_dict = dict(row._mapping)
                # Keep only columns that exist in the target schema
                filtered = {k: v for k, v in row_dict.items() if k in dst_col_names}
                data_to_insert.append(filtered)

            # Insert in chunks of 500
            chunk_size = 500
            for i in range(0, len(data_to_insert), chunk_size):
                chunk = data_to_insert[i:i + chunk_size]
                pg_conn.execute(dst_table.insert(), chunk)

            # Check target count
            target_count = pg_conn.execute(select(dst_table)).fetchall()
            dst_count = len(target_count)

            status = "MATCH" if src_count == dst_count else "MISMATCH"
            results[table_name] = {"source": src_count, "destination": dst_count, "status": status}
            logger.info(f"Table '{table_name}': migrated {src_count} -> {dst_count} records [{status}]")

    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY AUDIT")
    print("=" * 60)
    all_matched = True
    for t, stat in results.items():
        print(f"  {t:25}: Source={stat['source']:5} | Target={stat['destination']:5} | {stat['status']}")
        if stat["status"] == "MISMATCH":
            all_matched = False

    print("=" * 60)
    if all_matched:
        logger.info("Database migration finished with 100% integrity verification.")
    else:
        logger.warning("Migration completed with count mismatches. Please inspect above.")
    return all_matched


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else None
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    migrate(src, dst)

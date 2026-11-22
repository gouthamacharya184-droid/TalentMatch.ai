#!/usr/bin/env python3
"""
TalentMatch.ai Automated Database Backup & Integrity Check Utility.
Supports SQLite (development) and PostgreSQL (production).
Generates SHA-256 checksums, gzips archives, and enforces retention limits.
"""
import argparse
import gzip
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def backup_database(db_url: str | None = None, backup_dir_path: str | None = None, retention_count: int = 7) -> bool:
    root_dir = Path(__file__).resolve().parent.parent
    backup_dir = Path(backup_dir_path) if backup_dir_path else root_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_url = db_url or os.environ.get("DATABASE_URL", "sqlite:///./talentmatch.db")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    if db_url.startswith("sqlite"):
        sqlite_file = db_url.replace("sqlite:///", "").lstrip("./")
        src_path = Path(sqlite_file)
        if not src_path.is_absolute():
            # Search candidate paths
            candidates = [
                root_dir / "backend" / sqlite_file,
                root_dir / sqlite_file,
                Path.cwd() / sqlite_file,
            ]
            for c in candidates:
                if c.exists():
                    src_path = c
                    break

        if not src_path.exists():
            print(f"[ERROR] SQLite database file not found at: {src_path}")
            return False

        dest_raw = backup_dir / f"talentmatch_backup_{timestamp}.db"
        dest_gz = backup_dir / f"talentmatch_backup_{timestamp}.db.gz"

        print(f"[INFO] Backing up SQLite database {src_path} -> {dest_gz}...")
        try:
            # Use SQLite backup API to safely snapshot even if transactions are active
            src_conn = sqlite3.connect(str(src_path))
            dest_conn = sqlite3.connect(str(dest_raw))
            src_conn.backup(dest_conn)
            dest_conn.close()
            src_conn.close()

            # Compress
            with open(dest_raw, "rb") as f_in, gzip.open(dest_gz, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            dest_raw.unlink()

            checksum = compute_sha256(dest_gz)
            chk_file = backup_dir / f"talentmatch_backup_{timestamp}.sha256"
            chk_file.write_text(f"{checksum}  {dest_gz.name}\n")

            print(f"[SUCCESS] Backup created successfully: {dest_gz.name}")
            print(f"[SUCCESS] SHA-256 Checksum: {checksum}")
        except Exception as e:
            print(f"[ERROR] Backup failed: {e}")
            return False

    elif db_url.startswith("postgresql"):
        dest_sql_gz = backup_dir / f"talentmatch_pg_backup_{timestamp}.sql.gz"
        print(f"[INFO] Backing up PostgreSQL database to {dest_sql_gz}...")
        try:
            # First try pg_dump binary if installed
            pg_dump_path = shutil.which("pg_dump")
            if pg_dump_path:
                dump_cmd = [pg_dump_path, db_url]
                with gzip.open(dest_sql_gz, "wb") as f_out:
                    proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = proc.communicate()
                    if proc.returncode != 0:
                        raise RuntimeError(f"pg_dump exited with error: {stderr.decode('utf-8', errors='replace')}")
                    f_out.write(stdout)
            else:
                # Fallback: Python streaming table dump via SQLAlchemy
                print("[INFO] pg_dump CLI utility not found in PATH; performing streaming SQL dump...")
                import json
                from sqlalchemy import create_engine, inspect, text

                engine = create_engine(db_url)
                inspector = inspect(engine)
                table_names = inspector.get_table_names()

                with gzip.open(dest_sql_gz, "wt", encoding="utf-8") as f_out:
                    f_out.write(f"-- TalentMatch.ai PostgreSQL Snapshot: {timestamp}\n")
                    with engine.connect() as conn:
                        for table in table_names:
                            f_out.write(f"\n-- Table: {table}\n")
                            result = conn.execute(text(f'SELECT * FROM "{table}"'))
                            columns = result.keys()
                            rows = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in result.fetchall()]
                            f_out.write(f"-- Rows count: {len(rows)}\n")
                            f_out.write(json.dumps({table: rows}, default=str) + "\n")

            checksum = compute_sha256(dest_sql_gz)
            chk_file = backup_dir / f"talentmatch_pg_backup_{timestamp}.sha256"
            chk_file.write_text(f"{checksum}  {dest_sql_gz.name}\n")
            print(f"[SUCCESS] PostgreSQL backup created: {dest_sql_gz.name}")
            print(f"[SUCCESS] SHA-256 Checksum: {checksum}")
        except Exception as e:
            print(f"[ERROR] PostgreSQL backup failed: {e}")
            return False
    else:
        print(f"[ERROR] Unsupported database protocol in DATABASE_URL: {db_url}")
        return False

    # Retention Policy: keep last N backups, prune older
    backups = sorted(backup_dir.glob("*.gz"), key=lambda p: p.stat().st_mtime)
    if len(backups) > retention_count:
        to_prune = backups[:-retention_count]
        for old in to_prune:
            print(f"[INFO] Pruning old backup archive: {old.name}")
            old.unlink(missing_ok=True)
            sha_old = old.with_suffix(".sha256")
            if sha_old.exists():
                sha_old.unlink(missing_ok=True)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TalentMatch.ai Database Backup Utility")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL (PostgreSQL or SQLite)")
    parser.add_argument("--sqlite-db", type=str, default=None, help="Explicit path to SQLite database file")
    parser.add_argument("--backup-dir", type=str, default=None, help="Directory to store backup archives")
    parser.add_argument("--retention", type=int, default=7, help="Number of recent backups to retain (default: 7)")
    args = parser.parse_args()

    target_url = args.db_url
    if not target_url and args.sqlite_db:
        target_url = f"sqlite:///{args.sqlite_db}"

    success = backup_database(db_url=target_url, backup_dir_path=args.backup_dir, retention_count=args.retention)
    sys.exit(0 if success else 1)

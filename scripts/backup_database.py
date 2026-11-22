#!/usr/bin/env python3
"""
TalentMatch.ai Automated Database Backup & Integrity Check Utility.
Supports SQLite (development) and PostgreSQL (production).
Generates SHA-256 checksums, gzips archives, and enforces retention limits.
"""
import os
import sys
import gzip
import shutil
import hashlib
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def backup_database():
    root_dir = Path(__file__).resolve().parent.parent
    backup_dir = root_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./talentmatch.db")

    if db_url.startswith("sqlite"):
        sqlite_file = db_url.replace("sqlite:///", "").lstrip("./")
        src_path = root_dir / "backend" / sqlite_file
        if not src_path.exists():
            src_path = root_dir / sqlite_file
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

    elif db_url.startswith("postgres"):
        dest_sql_gz = backup_dir / f"talentmatch_pg_backup_{timestamp}.sql.gz"
        print(f"[INFO] Backing up PostgreSQL database to {dest_sql_gz}...")
        try:
            dump_cmd = ["pg_dump", db_url]
            with gzip.open(dest_sql_gz, "wb") as f_out:
                proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    print(f"[ERROR] pg_dump failed: {stderr.decode('utf-8')}")
                    return False
                f_out.write(stdout)

            checksum = compute_sha256(dest_sql_gz)
            chk_file = backup_dir / f"talentmatch_pg_backup_{timestamp}.sha256"
            chk_file.write_text(f"{checksum}  {dest_sql_gz.name}\n")
            print(f"[SUCCESS] PostgreSQL backup created: {dest_sql_gz.name}")
        except Exception as e:
            print(f"[ERROR] PostgreSQL backup failed: {e}")
            return False

    # Retention Policy: keep last 7 backups, prune older
    backups = sorted(backup_dir.glob("*.gz"), key=lambda p: p.stat().st_mtime)
    if len(backups) > 7:
        to_prune = backups[:-7]
        for old in to_prune:
            print(f"[INFO] Pruning old backup archive: {old.name}")
            old.unlink(missing_ok=True)
            sha_old = old.with_suffix(".sha256")
            if sha_old.exists():
                sha_old.unlink()

    return True


if __name__ == "__main__":
    success = backup_database()
    sys.exit(0 if success else 1)

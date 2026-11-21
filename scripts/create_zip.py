import os
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "TalentMatch_AI_Complete_Project.zip")

EXCLUDE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".gemini",
    "dist"
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".DS_Store"
}

EXCLUDE_FILES = {
    "TalentMatch_AI_Complete_Project.zip",
    "talentmatch.db",  # Exclude local SQLite binary db so users seed fresh or run migrations
    ".env",            # Security: Never package secrets or live API keys
}

def should_exclude(dirpath, filename):
    for part in dirpath.split(os.sep):
        if part in EXCLUDE_DIRS:
            return True
    if filename in EXCLUDE_FILES:
        return True
    ext = os.path.splitext(filename)[1].lower()
    if ext in EXCLUDE_EXTENSIONS:
        return True
    return False

def make_zip():
    print(f"Creating {OUTPUT_ZIP}...")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # prune excluded dirs in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if should_exclude(root, file):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                zipf.write(full_path, rel_path)
                file_count += 1
                total_uncompressed_bytes += os.path.getsize(full_path)

    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"Successfully packaged {file_count} files into {OUTPUT_ZIP}")
    print(f"Uncompressed size: {total_uncompressed_bytes / (1024 * 1024):.2f} MB")
    print(f"ZIP Archive size: {zip_size_mb:.2f} MB")

    # Verify ZIP integrity
    print("Verifying ZIP integrity...")
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zipf:
        bad_file = zipf.testzip()
        if bad_file:
            raise RuntimeError(f"Corrupted file found in ZIP: {bad_file}")
        namelist = zipf.namelist()
        print(f"Verified ZIP archive contains {len(namelist)} items cleanly without corruption.")
        
        # Check critical files
        critical_files = [
            "backend/app/main.py",
            "backend/app/ai_engine/matching_engine.py",
            "backend/app/ai_engine/embeddings.py",
            "backend/app/parsers/resume_parser.py",
            "backend/requirements.txt",
            "backend/Dockerfile",
            "backend/alembic.ini",
            "frontend/package.json",
            "frontend/Dockerfile",
            "frontend/src/App.tsx",
            "frontend/src/pages/DashboardPage.tsx",
            "docker-compose.yml",
            "README.md",
            "LICENSE",
            ".env.example"
        ]
        for cf in critical_files:
            assert cf.replace("/", os.sep) in [n.replace("/", os.sep) for n in namelist], f"Missing critical file: {cf}"
        print("All critical architecture files verified present in the ZIP archive!")

if __name__ == "__main__":
    make_zip()


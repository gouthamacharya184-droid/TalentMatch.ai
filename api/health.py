import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup Python path before importing backend modules
current_dir = Path(__file__).resolve().parent
candidate_dirs = [
    current_dir.parent / "backend",
    current_dir / "backend",
    Path.cwd() / "backend",
    Path("/var/task/backend"),
    Path("/var/task"),
    current_dir.parent,
    current_dir,
]

for candidate in candidate_dirs:
    if (candidate / "app" / "main.py").exists():
        p = str(candidate)
        if p not in sys.path:
            sys.path.insert(0, p)
        os.environ["PYTHONPATH"] = p
        break

root_dir = str(current_dir.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI(title="TalentMatch AI - Health")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
@app.get("/health")
def health():
    db_status = "connected"
    try:
        from app.database.session import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    is_prod = bool(os.environ.get("VERCEL"))
    return {
        "status": "ok",
        "service": "TalentMatch AI",
        "version": "1.0.0",
        "environment": "production" if is_prod else "development",
        "database": db_status
    }

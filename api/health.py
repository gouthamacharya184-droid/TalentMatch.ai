import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup Python path before anything else
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

@app.get("/api/debug-import")
def debug_import():
    import traceback
    logs = []
    modules_to_test = [
        "app.core.config",
        "app.database.session",
        "app.database.seed",
        "app.models.all_models",
        "app.schemas.all_schemas",
        "app.api.deps",
        "app.api.auth",
        "app.api.jobs",
        "app.api.resumes",
        "app.api.candidates",
        "app.api.matching",
        "app.api.comparison",
        "app.api.shortlist",
        "app.api.analytics",
        "app.api.notifications",
        "app.api.chatbot",
        "app.api.campaigns",
        "app.api.interview_kits",
        "app.api.agents",
        "app.main",
    ]
    for mod_name in modules_to_test:
        try:
            logs.append(f"Importing {mod_name}...")
            __import__(mod_name)
            logs.append(f"SUCCESS: {mod_name}")
        except Exception as e:
            return {
                "status": "failed",
                "failed_module": mod_name,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "logs": logs,
                "sys_path": sys.path[:5]
            }
    return {
        "status": "all_passed",
        "logs": logs,
        "sys_path": sys.path[:5]
    }

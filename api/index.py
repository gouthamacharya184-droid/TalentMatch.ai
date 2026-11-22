import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Top-level ASGI FastAPI app explicitly detected by Vercel static inspection
app = FastAPI(
    title="TalentMatch AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
@app.get("/health")
def health_endpoint():
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

@app.get("/api/ping")
@app.get("/ping")
def ping_endpoint():
    return {"ok": True}

# Locate backend directory across local, Docker, and Vercel environments
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

backend_dir = None
for candidate in candidate_dirs:
    if (candidate / "app" / "main.py").exists():
        backend_dir = candidate
        break

if backend_dir:
    backend_path = str(backend_dir)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    os.environ["PYTHONPATH"] = backend_path

root_dir = str(current_dir.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app.main import app as backend_app
    app.include_router(backend_app.router)
except Exception as _init_err:
    @app.get("/api/init-error")
    def init_error_debug():
        return {
            "error": "Backend app import failed",
            "detail": str(_init_err),
            "candidate_dirs": [str(d) for d in candidate_dirs],
            "sys_path": sys.path[:5]
        }

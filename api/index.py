import os
import sys
from pathlib import Path

# Dynamically locate the backend directory across environments
current_dir = Path(__file__).resolve().parent

candidate_dirs = [
    current_dir.parent / "backend",
    current_dir / "backend",
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
else:
    fallback = str(current_dir.parent / "backend")
    if fallback not in sys.path:
        sys.path.insert(0, fallback)
    os.environ["PYTHONPATH"] = fallback

# Ensure project root is also available for asset lookups
root_dir = str(current_dir.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app.main import app
except Exception as _init_err:
    import traceback
    _err_tb = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="TalentMatch AI - Diagnostic")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    @app.get("/health")
    @app.get("/api/ping")
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def fallback_handler(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "FastAPI Backend Initialization Failed on Vercel",
                "detail": str(_init_err),
                "traceback": _err_tb,
                "current_dir": str(current_dir),
                "candidate_dirs_checked": [str(d) for d in candidate_dirs],
                "sys_path": sys.path[:5],
                "files_in_current": [f.name for f in current_dir.iterdir()] if current_dir.exists() else [],
                "files_in_parent": [f.name for f in current_dir.parent.iterdir()] if current_dir.parent.exists() else []
            }
        )

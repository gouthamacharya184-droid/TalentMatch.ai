import os
import sys
from pathlib import Path

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
else:
    fallback = str(current_dir.parent / "backend")
    if fallback not in sys.path:
        sys.path.insert(0, fallback)
    os.environ["PYTHONPATH"] = fallback

root_dir = str(current_dir.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app.main import app
except Exception as _init_err:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="TalentMatch AI - Health Fallback")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    @app.get("/health")
    def fallback_health():
        return {
            "status": "ok",
            "service": "TalentMatch AI",
            "version": "1.0.0",
            "init_error": str(_init_err),
            "fallback": True
        }

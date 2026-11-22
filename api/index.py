import os
import sys
import traceback
from pathlib import Path

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

try:
    from app.main import app
except Exception as _e:
    _tb = traceback.format_exc()
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

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    def err(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Backend App Initialization Failed on Vercel",
                "detail": str(_e),
                "traceback": _tb,
                "sys_path": sys.path[:5]
            }
        )

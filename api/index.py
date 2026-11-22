import os
import sys
import traceback
from pathlib import Path

# Setup python path for backend
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("PYTHONPATH", str(BACKEND_DIR))

try:
    from app.main import app
except Exception as _init_err:
    _err_tb = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="TalentMatch AI - Diagnostic")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def fallback_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "FastAPI Initialization Failed on Vercel",
                "detail": str(_init_err),
                "traceback": _err_tb,
                "root_dir_contents": os.listdir(str(ROOT_DIR)) if ROOT_DIR.exists() else []
            }
        )

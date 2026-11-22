import os
import sys
import json
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
    from app.main import app as raw_app

    class SafeASGIApp:
        def __init__(self, inner):
            self.inner = inner

        async def __call__(self, scope, receive, send):
            if scope.get("type") == "http":
                headers = dict(scope.get("headers", []))
                matched_bytes = headers.get(b"x-matched-path") or headers.get(b"x-forwarded-uri") or b""
                matched_path = matched_bytes.decode("utf-8") if isinstance(matched_bytes, bytes) else str(matched_bytes)
                if matched_path:
                    clean = matched_path.split("?")[0]
                    if clean and scope.get("path") in ("/api/backend", "/api/index", "/api"):
                        scope["path"] = clean

                try:
                    await self.inner(scope, receive, send)
                except Exception as exc:
                    tb = traceback.format_exc()
                    err_payload = json.dumps({
                        "status": "error",
                        "error": "Unhandled Serverless Exception",
                        "detail": str(exc),
                        "traceback": tb,
                        "path": scope.get("path")
                    }).encode("utf-8")
                    await send({
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(err_payload)).encode("utf-8")),
                        ],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": err_payload,
                    })
            else:
                await self.inner(scope, receive, send)

    app = SafeASGIApp(raw_app)

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

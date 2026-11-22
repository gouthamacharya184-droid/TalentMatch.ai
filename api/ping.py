import json
from http.server import BaseHTTPRequestHandler

# FastAPI ASGI application definition
try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="TalentMatch AI - Canary Ping")

    @app.get("/api/ping")
    @app.get("/ping")
    def ping():
        return {"ok": True}
except Exception:
    app = None


# BaseHTTPRequestHandler definition for low-level serverless runner compatibility
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

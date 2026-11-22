from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TalentMatch AI - Canary Ping")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/ping")
@app.get("/ping")
def ping():
    return {"ok": True}

@app.get("/api/health")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "TalentMatch AI",
        "version": "1.0.0"
    }

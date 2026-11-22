import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TalentMatch AI - Canary Ping")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ping")
@app.get("/ping")
def ping():
    cur = Path(__file__).resolve().parent
    par = cur.parent
    return {
        "ok": True,
        "current_dir": str(cur),
        "parent_dir": str(par),
        "parent_files": [f.name for f in par.iterdir()] if par.exists() else [],
        "cwd": os.getcwd(),
        "cwd_files": os.listdir(os.getcwd()) if os.path.exists(os.getcwd()) else []
    }

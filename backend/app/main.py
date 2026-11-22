import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agents import router as agents_router
from app.api.analytics import router as analytics_router

# Routers
from app.api.auth import router as auth_router
from app.api.campaigns import router as campaigns_router
from app.api.candidates import router as candidates_router
from app.api.chatbot import router as chatbot_router
from app.api.comparison import router as comparison_router
from app.api.interview_kits import router as interview_kits_router
from app.api.jobs import router as jobs_router
from app.api.matching import router as matching_router
from app.api.notifications import router as notifications_router
from app.api.resumes import router as resumes_router
from app.api.shortlist import router as shortlist_router
from app.core.config import settings
from app.core.rate_limiter import RateLimitMiddleware
from app.database.seed import seed_database
from app.database.session import Base, SessionLocal, engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("talentmatch")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed safely
    logger.info("Initializing TalentMatch AI Database schema...")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Error creating database tables on startup: {e}")

    try:
        db = SessionLocal()
        seed_database(db, fast_mode=bool(os.environ.get("VERCEL")))
        db.close()
    except Exception as e:
        logger.warning(f"Error seeding database: {e}")

    logger.info("TalentMatch AI backend started successfully.")
    yield
    logger.info("Shutting down TalentMatch AI backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI-Powered Resume Matching & Candidate Ranking Platform for AVOM Consultants",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

# CORS Middleware with valid origins and credentials support
raw_allowed = os.environ.get("ALLOWED_ORIGINS", "")
custom_origins = [o.strip() for o in raw_allowed.split(",") if o.strip()] if raw_allowed else []

allowed_origins = list(
    dict.fromkeys(
        custom_origins
        + settings.CORS_ORIGINS
        + [
            settings.FRONTEND_URL,
            "http://localhost",
            "http://localhost:80",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Automated Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)


# Request Correlation ID & Performance Observability Middleware
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = req_id
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    return response


# Enterprise Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; frame-ancestors 'none';"
    )
    return response


# Vercel Serverless Path Rewriter Middleware
@app.middleware("http")
async def fix_vercel_rewritten_paths(request: Request, call_next):
    # When Vercel rewrites /api/* to /api/index.py, x-matched-path holds the original client URL
    matched = request.headers.get("x-matched-path") or request.headers.get("x-forwarded-uri")
    current_path = request.scope.get("path", "")
    if matched and current_path in ("/api/backend", "/api/index.py", "/api/index", "/index.py", "/api"):
        clean_path = matched.split("?")[0]
        if clean_path:
            request.scope["path"] = clean_path
    return await call_next(request)


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())
    is_debug = bool(settings.DEBUG and os.environ.get("ENVIRONMENT") != "production" and not os.environ.get("VERCEL"))
    content = {
        "detail": "Not Found",
        "path": request.url.path,
        "request_id": req_id,
    }
    if is_debug:
        content["scope_path"] = request.scope.get("path")
        content["x_matched_path"] = request.headers.get("x-matched-path")
        content["x_forwarded_uri"] = request.headers.get("x-forwarded-uri")
    return JSONResponse(status_code=404, content=content)


@app.exception_handler(Exception)
async def custom_500_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())
    logger.exception(f"Unhandled error handling {request.method} {request.url.path} [Request-ID: {req_id}]: {exc}")
    is_debug = bool(settings.DEBUG and os.environ.get("ENVIRONMENT") != "production" and not os.environ.get("VERCEL"))
    content = {
        "detail": "Internal Server Error"
        if is_debug
        else "An unexpected internal server error occurred. Please contact support.",
        "request_id": req_id,
        "path": request.url.path,
    }
    if is_debug:
        content["error"] = str(exc)
        content["type"] = type(exc).__name__
    return JSONResponse(status_code=500, content=content)


# Mount Routers for both /api and /api/v1
routers = [
    auth_router,
    campaigns_router,
    jobs_router,
    resumes_router,
    candidates_router,
    matching_router,
    comparison_router,
    shortlist_router,
    analytics_router,
    notifications_router,
    chatbot_router,
    interview_kits_router,
    agents_router,
]
# Ensure primary API paths (/api, /api/v1) and bare paths are supported without duplicate registrations
api_prefixes = list(dict.fromkeys(["", settings.API_V1_STR, "/api/v1"]))
for prefix in api_prefixes:
    for r in routers:
        app.include_router(r, prefix=prefix)


# Health Check & Root
@app.post("/job-descriptions/parse")
@app.post("/api/job-descriptions/parse")
async def parse_job_description_endpoint(file: UploadFile = File(...)):
    from app.api.jobs import upload_job_document

    res = await upload_job_document(file)
    reqs = res.get("requirements", [])
    skills = [r.get("skill_name") if isinstance(r, dict) else getattr(r, "skill_name", str(r)) for r in reqs]
    return {
        "title": res.get("title", "Custom Job Description"),
        "description": res.get("description", ""),
        "skills": skills,
        **res,
    }


def _get_health_data():
    from app.database.session import SessionLocal, engine
    from app.models.all_models import Candidate, Resume, User

    user_count = 0
    candidate_count = 0
    resume_count = 0
    db_status = "connected"
    try:
        from app.api.deps import ensure_db_initialized

        ensure_db_initialized()
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            candidate_count = db.query(Candidate).count()
            resume_count = db.query(Resume).count()
        finally:
            db.close()
    except Exception as e:
        db_status = f"disconnected: {e!s}"

    is_prod = bool(os.environ.get("VERCEL")) or os.environ.get("ENVIRONMENT") == "production"
    dialect = getattr(engine.dialect, "name", "sqlite").lower()

    if is_prod and dialect == "sqlite":
        logger.critical(
            "CRITICAL WARNING: Database engine is SQLite in a serverless production environment! "
            "Data in /tmp does not persist across container cold starts. Configure DATABASE_URL with PostgreSQL."
        )

    has_blob = bool(getattr(settings, "BLOB_READ_WRITE_TOKEN", None) or os.environ.get("BLOB_READ_WRITE_TOKEN"))
    storage = "blob" if has_blob else "tmp (not persistent)"

    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "production" if is_prod else "development",
        "database": db_status,
        "db_engine": dialect,
        "storage": storage,
        "users": user_count,
        "candidates": candidate_count,
        "resumes": resume_count,
    }


@app.get("/health")
def root_health_check():
    data = _get_health_data()
    return {"status": "healthy" if data["database"] == "connected" else "degraded", **data}


@app.get("/api/health")
def api_health_check():
    data = _get_health_data()
    return {"status": "ok", **data}


@app.get("/")
def root():
    return {
        "product": "TalentMatch AI",
        "tagline": "Smarter Hiring. Better Matching. Faster Decisions.",
        "documentation": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

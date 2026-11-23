import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db

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
from app.core.logging_config import setup_structured_logging
from app.core.rate_limiter import RateLimitMiddleware
from app.core.security import cleanup_expired_revoked_tokens
from app.database.seed import seed_database
from app.database.session import Base, SessionLocal, engine

# Configure Structured JSON Logging with PII masking and optional Sentry
logger = setup_structured_logging("talentmatch")


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
        # Startup task: cleanup expired revoked tokens to prevent unbounded table growth
        cleanup_expired_revoked_tokens(db)
        db.close()
    except Exception as e:
        logger.warning(f"Error during startup database initialization: {e}")

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
    # HSTS without preload per security audit specification
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Content-Security-Policy with optional Report-Only mode
    csp_policy = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:; "
        "frame-ancestors 'none';"
    )
    if os.environ.get("CSP_REPORT_ONLY"):
        response.headers["Content-Security-Policy-Report-Only"] = csp_policy
    else:
        response.headers["Content-Security-Policy"] = csp_policy
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
    is_prod = bool(os.environ.get("VERCEL")) or os.environ.get("ENVIRONMENT") == "production"
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
        logger.error(f"Error checking database health: {e}")
        db_status = "disconnected" if is_prod else f"disconnected: {e!s}"

    dialect = getattr(engine.dialect, "name", "sqlite").lower()

    if is_prod and dialect == "sqlite":
        logger.critical(
            "CRITICAL WARNING: Database engine is SQLite in a serverless production environment! "
            "Data in /tmp does not persist across container cold starts. Configure DATABASE_URL with PostgreSQL."
        )

    has_blob = bool(getattr(settings, "BLOB_READ_WRITE_TOKEN", None) or os.environ.get("BLOB_READ_WRITE_TOKEN"))
    storage = "blob" if has_blob else "tmp (not persistent)"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
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


@app.get("/ping")
@app.get("/api/ping")
def canary_ping():
    """Lightweight canary ping probe for serverless and uptime monitors."""
    return {"ok": True}


@app.get("/health")
def liveness_check():
    """Pure liveness probe - returns 200 without database access."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "production"
        if (os.environ.get("VERCEL") or os.environ.get("ENVIRONMENT") == "production")
        else "development",
    }


@app.get("/api/health")
def health_check():
    """Observability check reporting database connection status and service metadata."""
    data = _get_health_data()
    status_code = 200 if data["database"] == "connected" else 503
    return JSONResponse(status_code=status_code, content=data)


@app.get("/api/cron/cleanup-tokens")
@app.post("/api/cron/cleanup-tokens")
def cron_cleanup_tokens(request: Request, db: Session = Depends(get_db)):
    """Scheduled task for Vercel Cron or background orchestrator to cleanup expired revoked tokens."""
    cron_secret = os.environ.get("CRON_SECRET")
    is_vercel = bool(request.headers.get("x-vercel-cron"))
    auth_header = request.headers.get("authorization", "")
    if cron_secret and not is_vercel and auth_header != f"Bearer {cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized cron invocation")

    count = cleanup_expired_revoked_tokens(db)
    logger.info(f"Cron token cleanup completed: {count} expired tokens purged.")
    return {"status": "success", "purged_count": count}


@app.get("/ready")
@app.get("/api/ready")
def readiness_check():
    """Readiness probe verifying live database connectivity."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected", "detail": str(e)},
        )


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

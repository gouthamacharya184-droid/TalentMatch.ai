import os
import tempfile
import uuid

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def _resolve_safe_upload_dir(raw_path: str | None = None) -> str:
    """Ensure upload directory is writable, falling back to /tmp in serverless or read-only environments."""
    is_serverless = bool(
        os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("LAMBDA_TASK_ROOT")
    )
    if is_serverless:
        tmp = os.path.join(tempfile.gettempdir(), "talentmatch_uploads")
        try:
            os.makedirs(tmp, exist_ok=True)
            return tmp
        except Exception:
            return tempfile.gettempdir()

    candidate = (
        raw_path or os.environ.get("UPLOAD_DIR") or os.path.join(os.path.dirname(__file__), "../../../storage/uploads")
    )
    try:
        abs_path = os.path.abspath(candidate)
        os.makedirs(abs_path, exist_ok=True)
        # Test write permission
        test_file = os.path.join(abs_path, f".test_{uuid.uuid4().hex[:6]}")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return abs_path
    except Exception:
        fallback = os.path.join(tempfile.gettempdir(), "talentmatch_uploads")
        try:
            os.makedirs(fallback, exist_ok=True)
            return fallback
        except Exception:
            return tempfile.gettempdir()


class Settings(BaseSettings):
    PROJECT_NAME: str = "TalentMatch AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./talentmatch.db", description="Database connection URL (PostgreSQL or SQLite)"
    )

    # Security & JWT
    SECRET_KEY: str = Field(
        default="talentmatch-super-secret-production-key-2026-secure-32-chars",
        description="Secret key for JWT generation",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Storage
    UPLOAD_DIR: str = Field(default_factory=_resolve_safe_upload_dir, description="Directory for uploaded resumes")
    MAX_FILE_SIZE_MB: float = 4.5 if os.environ.get("VERCEL") else 15.0
    MAX_BATCH_SIZE: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".doc", ".txt"]

    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def validate_upload_dir(cls, v: str) -> str:
        return _resolve_safe_upload_dir(v)

    # Vercel Blob Storage Integration
    BLOB_READ_WRITE_TOKEN: str | None = Field(
        default=None, description="Vercel Blob read-write access token for cloud resume persistence"
    )

    # AI Engine
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str | None = None
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Host & Port
    HOST: str = Field(
        default=os.environ.get("HOST", "127.0.0.1"),  # nosec B104
        description="Server host binding (defaults to loopback for security, configurable via HOST env)",
    )
    PORT: int = 8000
    ENVIRONMENT: str = Field(
        default="production"
        if os.environ.get("VERCEL") or os.environ.get("PRODUCTION")
        else os.environ.get("ENVIRONMENT", "development"),
        description="Runtime environment name",
    )
    DEBUG: bool = Field(
        default=False if os.environ.get("VERCEL") or os.environ.get("ENVIRONMENT") == "production" else True,
        description="Debug flag, explicitly disabled in production environments",
    )

    # Optional LLM Integration
    LLM_ENABLED: bool = True
    LLM_API_KEY: str | None = None
    LLM_MODEL: str | None = "gemini-2.5-flash"
    DAILY_AI_QUOTA_PER_USER: int = Field(default=50, description="Daily LLM request quota per user")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

# In production on Vercel, warn clearly if SECRET_KEY is not custom configured
if os.environ.get("VERCEL"):
    insecure_keys = {
        "default_secret_key",
        "change-me-in-production",
        "",
    }
    if not settings.SECRET_KEY or settings.SECRET_KEY in insecure_keys:
        import logging

        logging.getLogger("talentmatch").warning(
            "SECURITY WARNING: Custom SECRET_KEY environment variable is not configured in Vercel. "
            "Using default platform signing key. Configure SECRET_KEY in Vercel Project Settings for production security."
        )

# Ensure upload directory exists safely
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except OSError:
    pass

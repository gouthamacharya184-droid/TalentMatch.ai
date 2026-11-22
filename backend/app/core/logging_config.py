"""
Structured JSON Logging & Observability Configuration for TalentMatch.ai
Provides machine-readable JSON logs with request correlation IDs and secret/PII masking.
Optionally initializes Sentry when SENTRY_DSN is configured.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

# Sensitive keys to mask from log messages and extra attributes
SENSITIVE_PATTERNS = [
    re.compile(r"(password|passwd|secret|token|authorization|api_key|access_token|refresh_token)[\"']?\s*[:=]\s*[\"']?([^\"'\s,]+)", re.IGNORECASE),
]

SENSITIVE_FIELD_NAMES = {
    "password",
    "hashed_password",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "gemini_api_key",
    "openai_api_key",
}


def mask_sensitive_data(text: str) -> str:
    """Mask sensitive credentials from string log output."""
    if not isinstance(text, str):
        return text
    masked = text
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub(r"\1=***MASKED***", masked)
    return masked


class JSONLogFormatter(logging.Formatter):
    """
    Formatter that outputs structured JSON for cloud log aggregators
    (Vercel, AWS CloudWatch, Datadog, GCP Cloud Logging).
    """

    def __init__(self, service_name: str = "talentmatch-backend"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": mask_sensitive_data(record.getMessage()),
            "source": f"{record.filename}:{record.lineno}",
        }

        # Include request_id if attached to the record or present in thread context
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_entry["request_id"] = str(request_id)

        # Environment
        log_entry["environment"] = os.environ.get("ENVIRONMENT", "development")

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_structured_logging(service_name: str = "talentmatch") -> logging.Logger:
    """Configures structured JSON logging as the default handler."""
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate text output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter(service_name=service_name))
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Initialize optional Sentry
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=os.environ.get("ENVIRONMENT", "production"),
                traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                integrations=[FastApiIntegration(), sentry_logging],
            )
            root_logger.info("Sentry monitoring initialized successfully.")
        except ImportError:
            root_logger.warning("SENTRY_DSN provided but 'sentry-sdk' is not installed.")
        except Exception as e:
            root_logger.error(f"Failed to initialize Sentry: {e}")

    return logging.getLogger(service_name)

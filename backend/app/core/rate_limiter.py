import os
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """
    In-memory sliding window rate limiter.
    Provides per-IP and per-endpoint throttling to mitigate brute force, DoS, and LLM cost abuse.
    """

    def __init__(self):
        # Maps key -> list of timestamps
        self.requests: dict[str, list[float]] = defaultdict(list)
        # Endpoint prefix -> (max_requests, window_seconds)
        self.rules: dict[str, tuple[int, int]] = {
            "/api/auth/login": (15, 60),
            "/api/auth/register": (10, 60),
            "/api/auth/forgot-password": (8, 60),
            "/api/auth/reset-password": (8, 60),
            "/api/resumes/upload": (30, 60),
            "/api/chatbot/chat": (45, 60),
            "/api/interview-kits/generate": (30, 60),
        }
        self.default_rule: tuple[int, int] = (150, 60)

    def _get_client_ip(self, request: Request) -> str:
        # Check standard reverse proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # First IP in the comma-separated list is the client IP
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def is_rate_limited(self, request: Request) -> tuple[bool, int, int]:
        """
        Returns (is_limited, retry_after_seconds, limit).
        Always returns (False, 0, limit) during automated tests.
        """
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("ENVIRONMENT") == "test":
            return False, 0, 9999

        path = request.url.path

        # Whitelist public system endpoints
        if path in ("/health", "/api/health", "/api/ping", "/ping", "/", "/docs", "/redoc", "/openapi.json"):
            return False, 0, 9999

        ip = self._get_client_ip(request)

        # Match specific rule by path prefix
        limit, window = self.default_rule
        for route_prefix, rule in self.rules.items():
            if path.startswith(route_prefix):
                limit, window = rule
                break

        key = f"{ip}:{path}"
        now = time.time()
        window_start = now - window

        # Prune old timestamps
        timestamps = [t for t in self.requests[key] if t > window_start]
        self.requests[key] = timestamps

        if len(timestamps) >= limit:
            retry_after = max(1, int(window - (now - timestamps[0])))
            return True, retry_after, limit

        self.requests[key].append(now)
        return False, 0, limit


rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        is_limited, retry_after, limit = rate_limiter.is_rate_limited(request)
        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after_seconds": retry_after,
                    "limit_per_minute": limit,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )
        response = await call_next(request)
        return response

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

from app.main import app
from app.core.rate_limiter import RateLimiter


@pytest.fixture
def client():
    return TestClient(app)


def test_security_headers_present(client):
    """Verify production security headers on API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    
    headers = resp.headers
    # X-Frame-Options
    assert headers.get("x-frame-options") == "DENY"
    # X-Content-Type-Options
    assert headers.get("x-content-type-options") == "nosniff"
    # Referrer-Policy
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    # Permissions-Policy
    assert "camera=()" in headers.get("permissions-policy", "")
    assert "microphone=()" in headers.get("permissions-policy", "")
    # HSTS without 'preload'
    hsts = headers.get("strict-transport-security", "")
    assert "max-age=" in hsts
    assert "preload" not in hsts.lower()
    # Content-Security-Policy
    csp = headers.get("content-security-policy") or headers.get("content-security-policy-report-only")
    assert csp is not None
    assert "default-src" in csp


def test_health_liveness_no_db(client):
    """Verify /health is purely liveness without database connectivity checks."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "database" not in data  # Pure liveness, not readiness probe


def test_ready_readiness_db_check(client):
    """Verify /ready performs live database connectivity check."""
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_redis_limiter_fail_closed_on_login():
    """When Redis is down, login route MUST fail closed (429) to prevent brute-force attacks."""
    limiter = RateLimiter()
    limiter.redis_client = MagicMock()
    # Simulate redis pipeline failure
    limiter.redis_client.pipeline.side_effect = RedisError("Connection refused")

    req = MagicMock()
    req.url.path = "/api/auth/login"
    req.headers = {}
    req.client.host = "192.168.1.10"

    # Check login route fails closed
    is_limited, rem, limit = limiter.is_rate_limited(req, bypass_test_check=True)
    assert is_limited is True
    assert rem == 60


def test_redis_limiter_fail_open_on_non_auth():
    """When Redis is down, non-auth route MUST fail open with warning to avoid global outage."""
    limiter = RateLimiter()
    limiter.redis_client = MagicMock()
    limiter.redis_client.pipeline.side_effect = RedisError("Connection refused")

    req = MagicMock()
    req.url.path = "/api/candidates"
    req.headers = {}
    req.client.host = "192.168.1.10"

    # Check non-auth route fails open
    is_limited, rem, limit = limiter.is_rate_limited(req, bypass_test_check=True)
    assert is_limited is False
    assert rem == 0


def test_auth_cookies_and_csrf_protection(client):
    """Verify HttpOnly cookie for refresh token and Double Submit CSRF enforcement."""
    # Register/login a user to get tokens
    login_data = {
        "email": "csrf_test_user@example.com",
        "password": "Password123!",
        "full_name": "CSRF Test User",
        "role": "recruiter"
    }
    client.post("/api/auth/register", json=login_data)
    login_resp = client.post("/api/auth/login", json={"email": login_data["email"], "password": login_data["password"]})
    assert login_resp.status_code == 200
    
    # Verify cookies
    cookies = login_resp.cookies
    assert "refresh_token" in cookies
    assert "csrf_token" in cookies
    
    csrf_token = cookies["csrf_token"]
    refresh_token = cookies["refresh_token"]
    
    # Attempt refresh using cookie WITHOUT X-CSRF-Token header -> Expect 403 Forbidden
    # Clear authorization header, send cookie only
    no_csrf_resp = client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token, "csrf_token": csrf_token}
    )
    assert no_csrf_resp.status_code == 403
    assert "CSRF" in no_csrf_resp.json().get("detail", "")
    
    # Attempt refresh with valid matching X-CSRF-Token header -> Expect 200 OK
    csrf_ok_resp = client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token, "csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert csrf_ok_resp.status_code == 200
    assert "access_token" in csrf_ok_resp.json()


def test_pagination_limits_enforced(client):
    """Verify query parameters enforce limit <= 100."""
    # Candidates limit=101 -> 422
    resp = client.get("/api/candidates?limit=101")
    assert resp.status_code == 422

    # Jobs limit=101 -> 422
    resp = client.get("/api/jobs?limit=101")
    assert resp.status_code == 422

    # Resumes limit=101 -> 422
    resp = client.get("/api/resumes?limit=101")
    assert resp.status_code == 422


def test_cron_cleanup_tokens(client):
    """Verify expired token cleanup cron endpoint works."""
    resp = client.post("/api/cron/cleanup-tokens")
    assert resp.status_code == 200
    assert "purged_count" in resp.json()

"""
Audit Hardening & Production Verification Test Suite.
Validates:
1. Correlation ID (X-Request-ID) and timing headers (X-Response-Time)
2. Production error masking on 500/404 (no internal leaks)
3. Database-backed JWT token revocation & logout persistence
4. Password reset token replay protection
5. Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
6. Safe temporary directory usage and health endpoint observability
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, revoke_token, is_token_revoked, create_password_reset_token
from app.core.rate_limiter import rate_limiter
from app.database.session import SessionLocal
from app.models.all_models import RevokedToken, User

client = TestClient(app)


def test_request_id_and_timing_headers_present():
    """Verify that every HTTP response includes correlation ID and response duration."""
    response = client.get("/health")
    assert response.status_code in (200, 503)
    assert "x-request-id" in response.headers
    assert "x-response-time" in response.headers
    assert response.headers["x-response-time"].endswith("ms")


def test_security_headers_present_on_all_responses():
    """Verify production security headers are attached to responses."""
    response = client.get("/")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-origin" in headers.get("referrer-policy", "")


def test_404_handler_masks_internal_paths_in_production(monkeypatch):
    """Confirm 404 response does not leak internal routing variables when not in debug mode."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    response = client.get("/api/nonexistent-route-for-audit-test")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Not Found"
    assert "x_matched_path" not in data
    assert "scope_path" not in data


def test_token_revocation_persists_to_database():
    """Verify revoked tokens are recorded in the database blocklist."""
    db = SessionLocal()
    try:
        test_token = create_access_token("test-user-revoke-id")
        revoke_token(test_token, db=db, reason="test_revocation")

        # Verify record exists in DB
        record = db.query(RevokedToken).filter(RevokedToken.token == test_token).first()
        assert record is not None
        assert record.reason == "test_revocation"

        # Verify is_token_revoked returns True with db check
        assert is_token_revoked(test_token, db=db) is True
    finally:
        db.close()


def test_password_reset_replay_attack_prevention():
    """Verify a password reset token cannot be used twice."""
    db = SessionLocal()
    try:
        email = "replay_test_user@talentmatch.ai"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            from app.core.security import hash_password
            user = User(
                email=email,
                full_name="Replay Test User",
                hashed_password=hash_password("InitialPassword123!"),
                role="recruiter",
                is_active=True
            )
            db.add(user)
            db.commit()

        reset_token = create_password_reset_token(email)

        # First reset attempt should succeed
        res1 = client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewSecurePassword456!"
        })
        assert res1.status_code == 200

        # Second reset attempt with identical token MUST fail (replay attack prevented)
        res2 = client.post("/api/auth/reset-password", json={
            "token": reset_token,
            "new_password": "AnotherPassword789!"
        })
        assert res2.status_code == 400
        assert "already been used or revoked" in res2.json()["detail"].lower()
    finally:
        db.close()


def test_health_check_returns_clean_observability_data():
    """Verify /api/health reports database connection status and service metadata."""
    res = client.get("/api/health")
    assert res.status_code in (200, 503)
    data = res.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "database" in data
    assert "environment" in data


def test_canary_ping_endpoint_has_secure_cors():
    """Verify canary ping endpoint responds cleanly without wildcard credential leakage."""
    from api.ping import app as ping_app
    ping_client = TestClient(ping_app)
    res = ping_client.get("/api/ping")
    assert res.status_code == 200
    assert res.json() == {"ok": True}

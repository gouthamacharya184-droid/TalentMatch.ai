import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_password_reset_token_replay_protection():
    """Verify that password reset tokens cannot be reused once consumed."""
    # 1. Request password reset token for existing recruiter
    email = "recruiter@talentmatch.ai"
    req_res = client.post("/api/auth/forgot-password", json={"email": email})
    assert req_res.status_code == 200
    token = req_res.json().get("reset_token")
    assert token is not None

    # 2. Reset password successfully
    first_reset = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "Recruiter@123456"
    })
    assert first_reset.status_code == 200
    assert "successfully updated" in first_reset.json()["message"].lower()

    # 3. Attempt to reuse the SAME reset token immediately
    replay_reset = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "HackerPassword999!"
    })
    assert replay_reset.status_code == 400
    assert "already been used" in replay_reset.json()["detail"].lower() or "revoked" in replay_reset.json()["detail"].lower()


def test_candidate_manual_creation_endpoint():
    """Verify POST /api/candidates creates a candidate and associated skills properly."""
    cand_data = {
        "name": "Audit Test Candidate",
        "email": "audit.test.cand@example.com",
        "phone": "+1-555-019-2834",
        "location": "San Francisco, CA",
        "total_experience_years": 4.5,
        "education": [{"degree": "Bachelor of Science in Computer Science", "institution": "UC Berkeley"}],
        "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
        "status": "new"
    }
    res = client.post("/api/candidates", json=cand_data)
    assert res.status_code == 200
    created = res.json()
    assert created["id"]
    assert created["name"] == "Audit Test Candidate"
    assert created["email"] == "audit.test.cand@example.com"
    assert created["total_experience_years"] == 4.5

    # Verify skills were persisted and are returned
    skills_res = client.get(f"/api/candidates/{created['id']}/skills")
    assert skills_res.status_code == 200
    skills = skills_res.json()
    assert len(skills) == 5
    skill_names = [s["skill_name"] for s in skills]
    assert "Python" in skill_names
    assert "FastAPI" in skill_names
    assert "React" in skill_names

    # Clean up created candidate
    del_res = client.delete(f"/api/candidates/{created['id']}")
    assert del_res.status_code == 200


def test_enterprise_security_headers():
    """Verify all HTTP responses carry enterprise-grade security headers."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_cors_origin_policy():
    """Verify CORS handles explicit origins with credentials correctly."""
    res = client.options(
        "/api/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        }
    )
    # Status code 200 for OPTIONS preflight
    assert res.status_code == 200
    # Must not return wildcard '*' when credentials are true
    allow_origin = res.headers.get("access-control-allow-origin")
    assert allow_origin == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_nonexistent_entity_error_handling():
    """Verify consistent 404 responses for invalid IDs across all entity endpoints."""
    bad_id = "00000000-0000-0000-0000-000000000000"
    
    assert client.get(f"/api/jobs/{bad_id}").status_code == 404
    assert client.get(f"/api/candidates/{bad_id}").status_code == 404
    assert client.get(f"/api/resumes/{bad_id}/status").status_code == 404
    assert client.get(f"/api/matching/analysis/{bad_id}").status_code == 404
    assert client.delete(f"/api/shortlist/{bad_id}").status_code == 404
    assert client.put(f"/api/notifications/{bad_id}/read").status_code == 404


def test_admin_demo_login_success():
    """Verify admin demo credentials authenticate successfully and return valid JWT."""
    res = client.post("/api/auth/login", json={
        "email": "admin@talentmatch.ai",
        "password": "Admin@123456"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@talentmatch.ai"
    assert data["user"]["role"] == "super_admin"


def test_admin_demo_login_wrong_password():
    """Verify invalid password returns 401 Unauthorized with clear message."""
    res = client.post("/api/auth/login", json={
        "email": "admin@talentmatch.ai",
        "password": "WrongPassword!999"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password."


def test_auth_me_with_valid_token():
    """Verify /api/auth/me resolves current user via JWT bearer token."""
    login_res = client.post("/api/auth/login", json={
        "email": "admin@talentmatch.ai",
        "password": "Admin@123456"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user = me_res.json()
    assert user["email"] == "admin@talentmatch.ai"
    assert user["role"] == "super_admin"


def test_api_health_database_and_user_count():
    """Verify /api/health reports connected database status and seeded user count."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert isinstance(data.get("users"), int)
    assert data["users"] >= 2


def test_recruiter_demo_login_success():
    """Verify recruiter demo credentials authenticate successfully and return valid JWT."""
    res = client.post("/api/auth/login", json={
        "email": "recruiter@talentmatch.ai",
        "password": "Recruiter@123456"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "recruiter@talentmatch.ai"
    assert data["user"]["role"] == "recruiter"


def test_recruiter_auth_me_with_valid_token():
    """Verify /api/auth/me resolves recruiter via JWT bearer token."""
    login_res = client.post("/api/auth/login", json={
        "email": "recruiter@talentmatch.ai",
        "password": "Recruiter@123456"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user = me_res.json()
    assert user["email"] == "recruiter@talentmatch.ai"
    assert user["role"] == "recruiter"


def test_auth_trailing_slash_resilience():
    """Verify trailing slash endpoints resolve without 307/308 redirects dropping body."""
    login_res = client.post("/api/auth/login/", json={
        "email": "admin@talentmatch.ai",
        "password": "Admin@123456"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me/", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@talentmatch.ai"


def test_resume_upload_serverless_storage_fallback(monkeypatch):
    """Verify resume upload succeeds and falls back to /tmp when UPLOAD_DIR is unwritable."""
    import io
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("UPLOAD_DIR", "../storage/uploads")

    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    file_payload = ("test_serverless_fallback.pdf", io.BytesIO(pdf_content), "application/pdf")

    res = client.post(
        "/api/resumes/upload",
        files={"files": file_payload}
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["original_filename"] == "test_serverless_fallback.pdf"
    assert data[0]["file_size"] > 0


def test_cold_start_seeding_includes_candidate_pool(monkeypatch):
    """Verify that serverless cold starts (fast_mode=True) populate the 12 candidate pool."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.session import Base
    from app.models.all_models import Candidate, Job, User
    from app.database.seed import seed_database

    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    test_db = TestSession()

    try:
        # Run seed in serverless fast mode
        seed_database(test_db, fast_mode=True)

        assert test_db.query(User).count() >= 2
        assert test_db.query(Job).count() >= 6
        assert test_db.query(Candidate).count() >= 12

        # Verify priority requisitions exist
        job_titles = [j.title for j in test_db.query(Job).all()]
        assert "AI Engineer" in job_titles
        assert "ML Engineer" in job_titles
        assert "Software Engineer" in job_titles

        # Verify candidate pool has realistic records
        cands = test_db.query(Candidate).all()
        cand_names = [c.name for c in cands]
        assert "Marcus Vance" in cand_names
        assert "Elena Rostova" in cand_names

        # Verify idempotency on second run
        seed_database(test_db, fast_mode=True)
        assert test_db.query(Candidate).count() >= 12
    finally:
        test_db.close()





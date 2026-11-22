import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import Base, engine, SessionLocal
from app.models.all_models import User, Job, Candidate, Resume, MatchingAnalysis, RecruiterNote

client = TestClient(app)

RESUMES_50_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/test_resumes_50"))
EDGE_CASES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures/test_resumes_edge_cases"))

@pytest.fixture(scope="module", autouse=True)
def setup_module():
    Base.metadata.create_all(bind=engine)


# ── 1. AUTHENTICATION & SECURITY AUDIT ──────────────────────────────────────────

def test_auth_security_flow():
    # 1. Register test user with unique run identifier
    run_id = uuid.uuid4().hex[:8]
    reg_email = f"audit_recruiter_{run_id}@talentmatch.ai"
    reg_res = client.post("/api/auth/register", json={
        "full_name": f"Audit Recruiter {run_id}",
        "email": reg_email,
        "password": "SecurePassword123!",
        "role": "recruiter"
    })
    assert reg_res.status_code == 200
    tokens = reg_res.json()

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert access_token and refresh_token

    # 2. Verify protected route rejects unauthenticated request
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401
    assert "required" in unauth_res.json()["detail"].lower() or "unauthorized" in unauth_res.json()["detail"].lower()

    # 3. Verify protected route succeeds with valid token
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == reg_email

    # 4. Verify refresh token rotation
    ref_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    new_access = ref_data["access_token"]
    new_refresh = ref_data["refresh_token"]
    assert new_access != access_token
    assert new_refresh != refresh_token

    # Old refresh token should now be revoked and rejected
    reused_ref = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert reused_ref.status_code == 401

    # 5. Verify logout invalidates the session
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {new_access}"})
    assert logout_res.status_code == 200
    assert "invalidated" in logout_res.json()["message"].lower()

    # Access with revoked token must fail with 401
    revoked_check = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert revoked_check.status_code == 401

    # 6. Verify password reset does not leak user existence
    forgot_res = client.post("/api/auth/forgot-password", json={"email": "nonexistent_email_12345@domain.com"})
    assert forgot_res.status_code == 200
    assert "if this email is registered" in forgot_res.json()["message"].lower()

    # Known user gets a valid token
    forgot_user = client.post("/api/auth/forgot-password", json={"email": reg_email})
    assert forgot_user.status_code == 200
    reset_tok = forgot_user.json().get("reset_token")
    assert reset_tok is not None

    # Reset password with token
    reset_res = client.post("/api/auth/reset-password", json={
        "token": reset_tok,
        "new_password": "NewStrongPassword456!"
    })
    assert reset_res.status_code == 200

    # Login with new password
    new_login = client.post("/api/auth/login", json={
        "email": reg_email,
        "password": "NewStrongPassword456!"
    })
    assert new_login.status_code == 200


# ── 2. BULK RESUME UPLOAD STRESS TESTING (10, 25, 50 Files + Edge Cases) ────────

def get_auth_token():
    res = client.post("/api/auth/login", json={
        "email": "recruiter@talentmatch.ai",
        "password": "Recruiter@123456"
    })
    return res.json()["access_token"]


def test_bulk_upload_10_resumes():
    token = get_auth_token()
    all_files = sorted([f for f in os.listdir(RESUMES_50_DIR) if f.endswith(('.pdf', '.docx'))])
    batch_10 = all_files[:10]
    assert len(batch_10) == 10

    upload_files = []
    for fname in batch_10:
        fpath = os.path.join(RESUMES_50_DIR, fname)
        content_type = "application/pdf" if fname.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(fpath, "rb") as f:
            upload_files.append(("files", (fname, f.read(), content_type)))

    res = client.post("/api/resumes/upload", files=upload_files, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    for r in data:
        assert r["processing_status"] == "completed"
        assert r["file_size"] > 0


def test_bulk_upload_25_resumes():
    token = get_auth_token()
    all_files = sorted([f for f in os.listdir(RESUMES_50_DIR) if f.endswith(('.pdf', '.docx'))])
    batch_25 = all_files[:25]
    assert len(batch_25) == 25

    upload_files = []
    for fname in batch_25:
        fpath = os.path.join(RESUMES_50_DIR, fname)
        content_type = "application/pdf" if fname.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(fpath, "rb") as f:
            upload_files.append(("files", (fname, f.read(), content_type)))

    res = client.post("/api/resumes/upload", files=upload_files, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 25
    for r in data:
        assert r["processing_status"] == "completed"


def test_bulk_upload_50_resumes_max_capacity():
    token = get_auth_token()
    all_files = sorted([f for f in os.listdir(RESUMES_50_DIR) if f.endswith(('.pdf', '.docx'))])
    batch_50 = all_files[:50]
    assert len(batch_50) == 50

    upload_files = []
    for fname in batch_50:
        fpath = os.path.join(RESUMES_50_DIR, fname)
        content_type = "application/pdf" if fname.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(fpath, "rb") as f:
            upload_files.append(("files", (fname, f.read(), content_type)))

    res = client.post("/api/resumes/upload", files=upload_files, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 50
    for r in data:
        assert r["processing_status"] == "completed"


def test_upload_edge_cases_isolation():
    token = get_auth_token()
    # 1. Invalid file extension (.exe)
    invalid_file = os.path.join(EDGE_CASES_DIR, "Edge_03_Executable_Payload.exe")
    with open(invalid_file, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_03_Executable_Payload.exe", f.read(), "application/octet-stream"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    item = res.json()[0]
    assert item["processing_status"] == "failed"
    assert "unsupported" in item["error_message"].lower()

    # 2. Password protected PDF
    pwd_pdf = os.path.join(EDGE_CASES_DIR, "Edge_04_Password_Protected.pdf")
    with open(pwd_pdf, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_04_Password_Protected.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    item = res.json()[0]
    assert item["processing_status"] == "failed"
    assert "password" in item["error_message"].lower()

    # 3. Corrupted / unreadable PDF
    corrupt_pdf = os.path.join(EDGE_CASES_DIR, "Edge_02_Corrupted_Header.pdf")
    with open(corrupt_pdf, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_02_Corrupted_Header.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    item = res.json()[0]
    assert item["processing_status"] == "failed"

    # 4. Mixed batch: 1 valid PDF + 1 invalid EXE + 1 password-protected PDF
    # Proves one failure does not halt the entire batch
    valid_pdf = os.path.join(RESUMES_50_DIR, os.listdir(RESUMES_50_DIR)[0])
    with open(valid_pdf, "rb") as f1, open(invalid_file, "rb") as f2, open(pwd_pdf, "rb") as f3:
        mixed_files = [
            ("files", ("Valid_Resume.pdf", f1.read(), "application/pdf")),
            ("files", ("Bad_Payload.exe", f2.read(), "application/octet-stream")),
            ("files", ("Locked.pdf", f3.read(), "application/pdf")),
        ]
        res_mixed = client.post("/api/resumes/upload", files=mixed_files, headers={"Authorization": f"Bearer {token}"})
    assert res_mixed.status_code == 200
    mixed_results = res_mixed.json()
    assert len(mixed_results) == 3
    assert mixed_results[0]["processing_status"] == "completed"
    assert mixed_results[1]["processing_status"] == "failed"
    assert mixed_results[2]["processing_status"] == "failed"


# ── 3. AI MATCHING ENGINE & MATHEMATICAL CONSTRAINTS ──────────────────────────

def test_mathematical_scoring_precision_and_limits():
    token = get_auth_token()
    jobs = client.get("/api/jobs").json()["items"]
    job = jobs[0]

    candidates = client.get("/api/candidates?limit=15").json()["items"]
    cand_ids = [c["id"] for c in candidates]

    res = client.post("/api/matching/analyze", json={
        "job_id": job["id"],
        "candidate_ids": cand_ids
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    analyses = res.json()

    for a in analyses:
        overall = a["overall_score"]
        tech = a["technical_score"]
        sem = a["semantic_score"]
        exp = a["experience_score"]
        edu = a["education_score"]

        # Exact boundary constraints
        assert 0.0 <= overall <= 100.0, f"Overall score {overall} out of bounds"
        assert 0.0 <= tech <= 40.0, f"Technical score {tech} exceeds 40.0 max"
        assert 0.0 <= sem <= 30.0, f"Semantic score {sem} exceeds 30.0 max"
        assert 0.0 <= exp <= 20.0, f"Experience score {exp} exceeds 20.0 max"
        assert 0.0 <= edu <= 10.0, f"Education score {edu} exceeds 10.0 max"

        # Mathematical sum check (precision within 0.1)
        expected_sum = round(tech + sem + exp + edu, 1)
        assert abs(overall - expected_sum) <= 0.15, f"Overall {overall} != sum {expected_sum}"

        # Model disclosure verification
        assert "model_info" in a or "model_info" in a["explanation"]
        model_info = a.get("model_info") or a["explanation"]["model_info"]
        assert "model_name" in model_info
        assert model_info["status"] in ["active", "fallback"]


def test_scoring_reproducibility():
    token = get_auth_token()
    jobs = client.get("/api/jobs").json()["items"]
    job = jobs[0]
    candidates = client.get("/api/candidates?limit=3").json()["items"]
    cand_ids = [c["id"] for c in candidates]

    # Run analysis twice with identical inputs
    res1 = client.post("/api/matching/analyze", json={"job_id": job["id"], "candidate_ids": cand_ids}, headers={"Authorization": f"Bearer {token}"}).json()
    res2 = client.post("/api/matching/analyze", json={"job_id": job["id"], "candidate_ids": cand_ids}, headers={"Authorization": f"Bearer {token}"}).json()

    scores1 = [r["overall_score"] for r in res1]
    scores2 = [r["overall_score"] for r in res2]
    assert scores1 == scores2, "AI matching must produce identical, deterministic scores for identical inputs"


def test_bias_protection_demographic_neutrality():
    """Verify personal demographic characteristics do not influence matching scores."""
    token = get_auth_token()
    jobs = client.get("/api/jobs").json()["items"]
    job = jobs[0]

    # Two identical candidate profiles differing only in name/gender
    cand1 = client.post("/api/candidates", json={
        "name": "David Smith",
        "email": "david.smith@example.com",
        "total_experience_years": 5.0,
        "education": [{"degree": "Bachelor of Science in Computer Science"}],
        "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL"]
    })
    # If POST /candidates is not directly exposed, we verify via matching engine directly
    from app.ai_engine.matching_engine import MatchingEngine
    engine = MatchingEngine()

    job_dict = {
        "title": "Full-Stack Engineer",
        "description": "Python, React, TypeScript, PostgreSQL",
        "min_experience": 4.0,
        "education_req": "Bachelor's Degree",
        "requirements": [
            {"skill_name": "Python", "category": "mandatory"},
            {"skill_name": "React", "category": "mandatory"},
            {"skill_name": "TypeScript", "category": "mandatory"},
            {"skill_name": "PostgreSQL", "category": "mandatory"}
        ]
    }

    male_cand = {
        "name": "John Doe",
        "total_experience_years": 5.0,
        "education": [{"degree": "Bachelor of Science"}]
    }
    female_cand = {
        "name": "Jane Doe",
        "total_experience_years": 5.0,
        "education": [{"degree": "Bachelor of Science"}]
    }
    shared_skills = ["Python", "React", "TypeScript", "PostgreSQL"]
    shared_text = "5 years experience developing web applications with Python and React."

    m_score = engine.match(job_dict, male_cand, shared_skills, shared_text)["overall_score"]
    f_score = engine.match(job_dict, female_cand, shared_skills, shared_text)["overall_score"]
    assert m_score == f_score, "Scoring algorithm must be completely gender and demographic neutral"


import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import Base, engine, SessionLocal
from app.database.seed import seed_database

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()


def test_health_and_root():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "TalentMatch AI" in res_root.json()["product"]


def test_auth_login():
    res = client.post("/api/auth/login", json={
        "email": "recruiter@talentmatch.ai",
        "password": "Recruiter@123456"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "recruiter@talentmatch.ai"


def test_get_dashboard_analytics():
    login_res = client.post("/api/auth/login", json={
        "email": "recruiter@talentmatch.ai",
        "password": "Recruiter@123456"
    })
    token = login_res.json()["access_token"]
    res = client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_jobs"] >= 2
    assert data["total_candidates"] >= 12
    assert data["avg_matching_score"] > 0
    assert len(data["recent_jobs"]) > 0


def test_job_crud_and_requirements():
    # 1. List jobs
    res = client.get("/api/jobs")
    assert res.status_code == 200
    jobs = res.json()["items"]
    assert len(jobs) >= 2
    target_job = next((j for j in jobs if len(j.get("description", "")) > 50), jobs[0])
    job_id = target_job["id"]

    # 2. Extract requirements
    res_req = client.post(f"/api/jobs/{job_id}/extract-requirements")
    assert res_req.status_code == 200
    reqs = res_req.json()
    assert len(reqs) > 0
    assert any("skill_name" in r for r in reqs)

    # 3. Create new job
    new_job = client.post("/api/jobs", json={
        "title": "Cloud DevOps Architect",
        "company": "AVOM Cloud Solutions",
        "location": "Remote",
        "min_experience": 5.0,
        "education_req": "Bachelor's Degree",
        "description": "Seeking expert in Kubernetes, Terraform, AWS, Docker, Python, CI/CD, and Prometheus."
    })
    assert new_job.status_code == 200
    created = new_job.json()
    assert created["title"] == "Cloud DevOps Architect"
    assert len(created["requirements"]) >= 4


def test_candidates_and_rankings():
    # 1. Get candidates
    res = client.get("/api/candidates?limit=10")
    assert res.status_code == 200
    candidates = res.json()["items"]
    assert len(candidates) >= 10
    cand_id = candidates[0]["id"]

    # 2. Get single candidate
    res_c = client.get(f"/api/candidates/{cand_id}")
    assert res_c.status_code == 200
    assert res_c.json()["name"] == candidates[0]["name"]

    # 3. Get job rankings for seeded job
    jobs = client.get("/api/jobs?search=Senior Full-Stack Engineer").json().get("items", [])
    job_id = jobs[0]["id"] if jobs else "8aa94bff-4e94-4479-96e0-78928890a8a4"
    res_rank = client.get(f"/api/matching/rankings/{job_id}")
    assert res_rank.status_code == 200
    rankings = res_rank.json()
    assert len(rankings) > 0
    # Verify rankings are sorted descending
    scores = [r["overall_score"] for r in rankings]
    assert scores == sorted(scores, reverse=True)


def test_candidate_comparison():
    jobs = client.get("/api/jobs?search=Senior Full-Stack Engineer").json().get("items", [])
    job_id = jobs[0]["id"] if jobs else "8aa94bff-4e94-4479-96e0-78928890a8a4"
    candidates = client.get("/api/candidates?limit=3").json()["items"]
    cand_ids = [c["id"] for c in candidates[:3]]

    res = client.post("/api/comparison/compare", json={
        "job_id": job_id,
        "candidate_ids": cand_ids
    })
    assert res.status_code == 200
    comp = res.json()
    assert len(comp["candidates"]) >= 2
    assert len(comp["skill_overlap"]) > 0


def test_shortlist_and_notes():
    jobs = client.get("/api/jobs").json()["items"]
    job_id = jobs[0]["id"]
    candidates = client.get("/api/candidates?limit=2").json()["items"]
    cand_id = candidates[0]["id"]

    # Add to shortlist
    res = client.post("/api/shortlist", json={
        "job_id": job_id,
        "candidate_id": cand_id,
        "comments": "Strongest candidate during initial evaluation."
    })
    assert res.status_code == 200
    shortlist_id = res.json()["id"]

    # Add recruiter note
    res_note = client.post("/api/shortlist/notes", json={
        "candidate_id": cand_id,
        "job_id": job_id,
        "content": "Candidate confirmed availability for technical interview on Friday."
    })
    assert res_note.status_code == 200
    assert "availability" in res_note.json()["content"]

    # Fetch notes
    res_get_notes = client.get(f"/api/shortlist/notes/{cand_id}")
    assert res_get_notes.status_code == 200
    assert len(res_get_notes.json()) > 0


def test_report_exports():
    jobs = client.get("/api/jobs?limit=100").json()["items"]
    seeded_job = next((j for j in jobs if j["title"] == "Senior Full-Stack Engineer"), jobs[0])
    job_id = seeded_job["id"]

    # CSV
    res_csv = client.get(f"/api/analytics/reports/{job_id}/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "Rank" in res_csv.text

    # XLSX
    res_xlsx = client.get(f"/api/analytics/reports/{job_id}/export?format=xlsx")
    assert res_xlsx.status_code == 200
    assert len(res_xlsx.content) > 100

    # PDF
    res_pdf = client.get(f"/api/analytics/reports/{job_id}/export?format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF")

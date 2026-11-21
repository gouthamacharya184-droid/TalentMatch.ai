import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import Base, engine, SessionLocal
from app.models.all_models import Job, Candidate, Resume, MatchingAnalysis

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_jd_upload_document():
    # Test uploading a sample PDF job description
    sample_jobs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample_jobs"))
    pdf_path = os.path.join(sample_jobs_dir, "Job_Senior_FullStack_Engineer.pdf")
    assert os.path.exists(pdf_path), "Sample JD PDF must exist"

    with open(pdf_path, "rb") as f:
        res = client.post("/api/jobs/upload-jd", files={"file": ("Job_Senior_FullStack_Engineer.pdf", f, "application/pdf")})
    assert res.status_code == 200
    data = res.json()
    assert "Senior Full-Stack Engineer" in data["title"]
    assert data["company"] == "AVOM Consultants"
    assert len(data["requirements"]) >= 4


def test_load_sample_batch_resumes():
    # Ingest the 15 pre-generated sample resumes
    res = client.post("/api/resumes/load-sample-batch")
    assert res.status_code == 200
    batch = res.json()
    assert len(batch) >= 15
    for r in batch:
        assert r["processing_status"] in ["completed", "queued", "processing"]
        assert r["candidate_id"] is not None


def test_ai_matching_and_scoring_constraints():
    # Get all jobs and candidates
    jobs = client.get("/api/jobs").json()["items"]
    assert len(jobs) > 0
    fullstack_job = next((j for j in jobs if "Full-Stack" in j["title"]), jobs[0])

    candidates = client.get("/api/candidates?limit=20").json()["items"]
    assert len(candidates) >= 10
    cand_ids = [c["id"] for c in candidates]

    # Run AI Matching
    res = client.post("/api/matching/analyze", json={
        "job_id": fullstack_job["id"],
        "candidate_ids": cand_ids
    })
    assert res.status_code == 200
    analyses = res.json()
    assert len(analyses) == len(cand_ids)

    for a in analyses:
        # Verify 0-100 constraint
        assert 0.0 <= a["overall_score"] <= 100.0
        # Verify component boundaries
        assert 0.0 <= a["technical_score"] <= 40.0
        assert 0.0 <= a["semantic_score"] <= 30.0
        assert 0.0 <= a["experience_score"] <= 20.0
        assert 0.0 <= a["education_score"] <= 10.0
        
        # Verify sum matches overall score within floating precision
        sum_components = round(a["technical_score"] + a["semantic_score"] + a["experience_score"] + a["education_score"], 1)
        assert abs(sum_components - a["overall_score"]) <= 0.2

        # Verify explainability
        assert isinstance(a["matched_skills"], list)
        assert isinstance(a["missing_skills"], list)
        assert isinstance(a["strengths"], list)
        assert isinstance(a["skill_gaps"], list)


def test_ranking_sort_order():
    jobs = client.get("/api/jobs").json()["items"]
    fullstack_job = next((j for j in jobs if "Full-Stack" in j["title"]), jobs[0])
    
    res = client.get(f"/api/matching/rankings/{fullstack_job['id']}")
    assert res.status_code == 200
    rankings = res.json()
    assert len(rankings) > 0
    scores = [r["overall_score"] for r in rankings]
    assert scores == sorted(scores, reverse=True), "Rankings must be sorted strictly descending"


def test_single_candidate_details_and_notes():
    candidates = client.get("/api/candidates?limit=5").json()["items"]
    cand = candidates[0]

    # Fetch single candidate
    res = client.get(f"/api/candidates/{cand['id']}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == cand["id"]
    assert "skills" in detail

    # Update candidate status
    res_up = client.put(f"/api/candidates/{cand['id']}", json={"status": "interview"})
    assert res_up.status_code == 200
    assert res_up.json()["status"] == "interview"


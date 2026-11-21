"""
Comprehensive automated test suite for TalentMatch.ai v2.0 Enterprise Agentic Platform.
Validates the 8 specialized agents, criteria approval staging, What-If simulation engine,
page-level evidence citations, interview kits, campaigns, and observability telemetry.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_token():
    res = client.post("/api/auth/login", json={
        "email": "recruiter@talentmatch.ai",
        "password": "Recruiter@123456"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


def test_campaigns_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create campaign
    create_res = client.post("/api/campaigns", json={
        "name": "Q4 AI Platform Hiring Sprint",
        "department": "AI Engineering",
        "description": "Expanding the core agentic AI engineering team.",
        "target_hires": 5,
        "status": "active",
        "target_date": "2026-12-31"
    }, headers=headers)
    assert create_res.status_code == 200
    camp = create_res.json()
    assert camp["name"] == "Q4 AI Platform Hiring Sprint"
    camp_id = camp["id"]

    # 2. Get campaign
    get_res = client.get(f"/api/campaigns/{camp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["department"] == "AI Engineering"

    # 3. List campaigns
    list_res = client.get("/api/campaigns?limit=10")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(c["id"] == camp_id for c in items)

    # 4. Update campaign
    upd_res = client.put(f"/api/campaigns/{camp_id}", json={
        "target_hires": 8,
        "status": "active"
    })
    assert upd_res.status_code == 200
    assert upd_res.json()["target_hires"] == 8


def test_criteria_approval_workflow():
    # 1. Create a draft job
    res = client.post("/api/jobs", json={
        "title": "Agentic AI Architect",
        "company": "AVOM Consultants",
        "location": "Remote",
        "employment_type": "Full-time",
        "min_experience": 5.0,
        "education_req": "Bachelor's Degree in CS",
        "description": "Seeking an Agentic AI Architect skilled in Python, FastAPI, LangGraph, and PyTorch."
    })
    assert res.status_code == 200
    job = res.json()
    job_id = job["id"]
    assert job["criteria_approved"] is False

    # 2. Approve criteria with modified weights
    approve_res = client.post(f"/api/jobs/{job_id}/approve-criteria", json={
        "job_id": job_id,
        "approved": True,
        "requirements": [
            {"skill_name": "Python", "category": "mandatory", "skill_type": "language"},
            {"skill_name": "FastAPI", "category": "mandatory", "skill_type": "framework"},
            {"skill_name": "PyTorch", "category": "preferred", "skill_type": "framework"}
        ],
        "scoring_weights": {
            "required_skills": 40.0,
            "projects": 30.0,
            "experience": 15.0,
            "preferred_skills": 10.0,
            "education": 5.0
        }
    })
    assert approve_res.status_code == 200
    approved_job = approve_res.json()
    assert approved_job["criteria_approved"] is True
    assert approved_job["scoring_weights"]["projects"] == 30.0


def test_what_if_simulation_engine():
    # Get active job
    jobs = client.get("/api/jobs").json()["items"]
    assert len(jobs) > 0
    job = jobs[0]

    # Run what-if simulation with modified weights
    sim_res = client.post("/api/matching/what-if", json={
        "job_id": job["id"],
        "weights": {
            "required_skills": 50.0,
            "projects": 20.0,
            "experience": 10.0,
            "preferred_skills": 10.0,
            "education": 10.0
        },
        "modified_requirements": [
            {"skill_name": "FastAPI", "category": "mandatory", "skill_type": "framework"}
        ]
    })
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert "total_candidates_evaluated" in data
    assert "deltas" in data
    assert len(data["deltas"]) > 0
    first_delta = data["deltas"][0]
    assert "previous_score" in first_delta
    assert "simulated_score" in first_delta
    assert "rank_delta" in first_delta
    assert "impact_summary" in first_delta


def test_candidate_evidence_inspection():
    cands = client.get("/api/candidates?limit=5").json()["items"]
    assert len(cands) > 0
    cand = cands[0]

    res = client.get(f"/api/candidates/{cand['id']}/evidence")
    assert res.status_code == 200
    evidence_list = res.json()
    assert isinstance(evidence_list, list)
    if evidence_list:
        ev = evidence_list[0]
        assert "criterion" in ev
        assert "snippet" in ev
        assert "page_number" in ev
        assert "evidence_classification" in ev
        assert ev["page_number"] >= 1


def test_interview_kit_generation():
    jobs = client.get("/api/jobs").json()["items"]
    cands = client.get("/api/candidates?limit=5").json()["items"]
    assert len(jobs) > 0 and len(cands) > 0

    job_id = jobs[0]["id"]
    cand_id = cands[0]["id"]

    res = client.post("/api/interview-kits/generate", json={
        "candidate_id": cand_id,
        "job_id": job_id,
        "force_regenerate": True
    })
    assert res.status_code == 200
    kit = res.json()
    assert "questions" in kit
    assert len(kit["questions"]) >= 4
    first_q = kit["questions"][0]
    assert "category" in first_q
    assert "question" in first_q
    assert "expected_answer" in first_q
    assert "rubric_levels" in first_q
    assert "follow_up_probes" in first_q

    # Retrieve kit by endpoint
    get_res = client.get(f"/api/interview-kits/candidate/{cand_id}/job/{job_id}")
    assert get_res.status_code == 200
    assert len(get_res.json()["questions"]) >= 4


def test_agent_observability():
    # 1. Fetch agent executions list
    exec_res = client.get("/api/agents/executions?limit=10")
    assert exec_res.status_code == 200
    assert isinstance(exec_res.json(), list)

    # 2. Fetch agent aggregated telemetry stats
    stats_res = client.get("/api/agents/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_executions" in stats
    assert "active_agents" in stats
    assert "success_rate_percent" in stats
    assert "avg_latency_ms" in stats
    assert stats["active_agents"] >= 8

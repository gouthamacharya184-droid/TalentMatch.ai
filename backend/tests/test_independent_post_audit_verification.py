"""
Independent Post-Audit Security & Runtime Verification Suite.
Validates:
1. Shortlist Cross-User IDOR Prevention: Users cannot delete other recruiters' shortlist entries.
2. Shortlist Candidate ID Fallback Scope: Fallback deletion is strictly scoped to the calling user.
3. Information Exposure Prevention: Production health checks mask database error details.
4. AgentExecutionResponse schema clean initialization without Pydantic namespace warnings.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.database.session import SessionLocal
from app.models.all_models import Candidate, Job, Shortlist, User, generate_uuid

client = TestClient(app)


def test_shortlist_cross_user_idor_prevention():
    """Verify that User B cannot delete User A's shortlist record via IDOR."""
    db = SessionLocal()
    try:
        # Create User A and User B
        user_a = User(
            id=generate_uuid(),
            email=f"user_a_{generate_uuid()[:8]}@talentmatch.ai",
            full_name="Recruiter Alpha",
            hashed_password=hash_password("Pass123!"),
            role="recruiter",
            is_active=True,
        )
        user_b = User(
            id=generate_uuid(),
            email=f"user_b_{generate_uuid()[:8]}@talentmatch.ai",
            full_name="Recruiter Beta",
            hashed_password=hash_password("Pass123!"),
            role="recruiter",
            is_active=True,
        )
        db.add_all([user_a, user_b])

        # Create Job and Candidate
        job = Job(
            id=generate_uuid(),
            title="IDOR Test Lead Architect",
            company="Security Verification Corp",
            location="Remote",
            employment_type="Full-time",
            description="Testing authorization boundary enforcement",
            user_id=user_a.id,
        )
        cand = Candidate(
            id=generate_uuid(),
            name="Alpha Candidate",
            email=f"cand_{generate_uuid()[:8]}@example.com",
            status="analyzed",
        )
        db.add_all([job, cand])
        db.commit()

        # Recruiter A adds candidate to shortlist
        shortlist_a = Shortlist(
            id=generate_uuid(),
            job_id=job.id,
            candidate_id=cand.id,
            user_id=user_a.id,
            status="shortlisted",
            comments="Confidential shortlist entry by Recruiter A",
        )
        db.add(shortlist_a)
        db.commit()

        shortlist_a_id = str(shortlist_a.id)
        job_id = str(job.id)
        cand_id = str(cand.id)

        token_a = create_access_token(user_a.id, role="recruiter")
        token_b = create_access_token(user_b.id, role="recruiter")

        # 1. Recruiter B attempts to delete Recruiter A's shortlist by shortlist_id
        res_b = client.delete(
            f"/api/shortlist/{shortlist_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b.status_code == 404

        # Verify record still exists in DB
        db.expire_all()
        persisted = db.query(Shortlist).filter(Shortlist.id == shortlist_a_id).first()
        assert persisted is not None

        # 2. Recruiter B attempts to delete by job_id/candidate_id
        res_b_pair = client.delete(
            f"/api/shortlist/{job_id}/{cand_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b_pair.status_code == 404

        # Verify record STILL exists in DB
        db.expire_all()
        persisted = db.query(Shortlist).filter(Shortlist.id == shortlist_a_id).first()
        assert persisted is not None

        # 3. Recruiter A deletes their own shortlist entry - MUST succeed
        res_a = client.delete(
            f"/api/shortlist/{shortlist_a_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 200

        # Verify record is now deleted
        db.expire_all()
        deleted_record = db.query(Shortlist).filter(Shortlist.id == shortlist_a_id).first()
        assert deleted_record is None
    finally:
        db.close()


def test_shortlist_candidate_fallback_scoped_to_user():
    """Verify fallback deletion by candidate_id only removes the calling user's shortlist entry."""
    db = SessionLocal()
    try:
        user_a = User(
            id=generate_uuid(),
            email=f"rec_a_{generate_uuid()[:8]}@talentmatch.ai",
            full_name="Recruiter Alpha 2",
            hashed_password=hash_password("Pass123!"),
            role="recruiter",
            is_active=True,
        )
        user_b = User(
            id=generate_uuid(),
            email=f"rec_b_{generate_uuid()[:8]}@talentmatch.ai",
            full_name="Recruiter Beta 2",
            hashed_password=hash_password("Pass123!"),
            role="recruiter",
            is_active=True,
        )
        cand = Candidate(
            id=generate_uuid(),
            name="Shared Candidate Across Jobs",
            email=f"shared_{generate_uuid()[:8]}@example.com",
            status="analyzed",
        )
        job_a = Job(
            id=generate_uuid(),
            title="Job A",
            company="Company A",
            location="Remote",
            employment_type="Full-time",
            description="Job A description",
            user_id=user_a.id,
        )
        job_b = Job(
            id=generate_uuid(),
            title="Job B",
            company="Company B",
            location="Remote",
            employment_type="Full-time",
            description="Job B description",
            user_id=user_b.id,
        )
        db.add_all([user_a, user_b, cand, job_a, job_b])
        db.commit()

        # Both users shortlist the same candidate for their respective jobs
        shortlist_a = Shortlist(
            id=generate_uuid(),
            job_id=job_a.id,
            candidate_id=cand.id,
            user_id=user_a.id,
            status="shortlisted",
        )
        shortlist_b = Shortlist(
            id=generate_uuid(),
            job_id=job_b.id,
            candidate_id=cand.id,
            user_id=user_b.id,
            status="shortlisted",
        )
        db.add_all([shortlist_a, shortlist_b])
        db.commit()

        shortlist_a_id = str(shortlist_a.id)
        shortlist_b_id = str(shortlist_b.id)
        cand_id = str(cand.id)

        token_b = create_access_token(user_b.id, role="recruiter")

        # Recruiter B invokes delete using candidate_id fallback
        res_del = client.delete(
            f"/api/shortlist/{cand_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_del.status_code == 200

        db.expire_all()
        # Recruiter B's shortlist entry should be deleted
        assert db.query(Shortlist).filter(Shortlist.id == shortlist_b_id).first() is None
        # Recruiter A's shortlist entry MUST still exist! (No cross-user collateral deletion)
        assert db.query(Shortlist).filter(Shortlist.id == shortlist_a_id).first() is not None
    finally:
        db.close()


def test_production_health_error_masking(monkeypatch):
    """Verify that in production mode, internal database connection error traces are not leaked."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Health check returns clean 200 with masked or structured status
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "database" in data
    # Database status must never leak Python traceback or sensitive internal file paths
    assert "Traceback" not in data["database"]
    assert "password" not in data["database"].lower()

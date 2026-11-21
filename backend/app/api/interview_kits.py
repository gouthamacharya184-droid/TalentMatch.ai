from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_current_user
from app.models.all_models import InterviewKit, Candidate, Job, MatchingAnalysis, User, utc_now
from app.schemas.all_schemas import (
    InterviewKitResponse,
    InterviewKitGenerateRequest
)
from app.ai_engine.agents.interview_agent import InterviewIntelligenceAgent

router = APIRouter(prefix="/interview-kits", tags=["Interview Intelligence"])
interview_agent = InterviewIntelligenceAgent()


@router.post("/generate", response_model=InterviewKitResponse)
def generate_interview_kit(
    req: InterviewKitGenerateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get matched/missing skills from prior analysis if available
    analysis = db.query(MatchingAnalysis).filter(
        MatchingAnalysis.candidate_id == req.candidate_id,
        MatchingAnalysis.job_id == req.job_id
    ).first()

    matched_skills = [m.get("skill", "") if isinstance(m, dict) else str(m) for m in (analysis.matched_skills or [])] if analysis else [s.skill_name for s in candidate.skills[:5]]
    missing_skills = analysis.missing_skills if analysis else []

    cand_dict = {
        "id": candidate.id,
        "name": candidate.name,
        "total_experience_years": candidate.total_experience_years,
        "projects": candidate.projects or (candidate.extracted_profile.get("projects", []) if candidate.extracted_profile else []),
        "force_regenerate": req.force_regenerate
    }
    job_dict = {
        "id": job.id,
        "title": job.title,
        "description": job.description
    }

    kit_data = interview_agent.execute(
        candidate_data=cand_dict,
        job_data=job_dict,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        db=db,
        save_to_db=True
    )

    kit_data["candidate_name"] = candidate.name
    kit_data["job_title"] = job.title
    return kit_data


@router.get("/candidate/{candidate_id}/job/{job_id}", response_model=InterviewKitResponse)
def get_candidate_kit(
    candidate_id: str,
    job_id: str,
    db: Session = Depends(get_db)
):
    kit = db.query(InterviewKit).filter(
        InterviewKit.candidate_id == candidate_id,
        InterviewKit.job_id == job_id
    ).first()

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()

    if kit:
        return {
            "id": kit.id,
            "candidate_id": kit.candidate_id,
            "job_id": kit.job_id,
            "questions": kit.questions,
            "rubric_guidelines": kit.rubric_guidelines,
            "evaluation_notes": kit.evaluation_notes,
            "status": kit.status,
            "created_at": kit.created_at,
            "updated_at": kit.updated_at,
            "candidate_name": candidate.name if candidate else "Candidate",
            "job_title": job.title if job else "Position"
        }

    # Generate on-demand if not already generated
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")

    cand_dict = {
        "id": candidate.id,
        "name": candidate.name,
        "total_experience_years": candidate.total_experience_years,
        "projects": candidate.projects or (candidate.extracted_profile.get("projects", []) if candidate.extracted_profile else []),
    }
    job_dict = {"id": job.id, "title": job.title, "description": job.description}
    kit_data = interview_agent.execute(
        candidate_data=cand_dict,
        job_data=job_dict,
        matched_skills=[s.skill_name for s in candidate.skills[:5]],
        missing_skills=[],
        db=db,
        save_to_db=True
    )
    kit_data["candidate_name"] = candidate.name
    kit_data["job_title"] = job.title
    return kit_data


@router.get("/{kit_id}", response_model=InterviewKitResponse)
def get_interview_kit(kit_id: str, db: Session = Depends(get_db)):
    kit = db.query(InterviewKit).filter(InterviewKit.id == kit_id).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Interview kit not found")

    candidate = db.query(Candidate).filter(Candidate.id == kit.candidate_id).first()
    job = db.query(Job).filter(Job.id == kit.job_id).first()

    return {
        "id": kit.id,
        "candidate_id": kit.candidate_id,
        "job_id": kit.job_id,
        "questions": kit.questions,
        "rubric_guidelines": kit.rubric_guidelines,
        "evaluation_notes": kit.evaluation_notes,
        "status": kit.status,
        "created_at": kit.created_at,
        "updated_at": kit.updated_at,
        "candidate_name": candidate.name if candidate else "Candidate",
        "job_title": job.title if job else "Position"
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user
from app.models.all_models import User
from app.schemas.all_schemas import (
    MatchingAnalysisResponse,
    MatchRequest,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/matching", tags=["AI Matching"])
matching_service = MatchingService()


@router.post("/analyze", response_model=list[MatchingAnalysisResponse])
def analyze_match(
    req: MatchRequest, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        results = matching_service.analyze_match(
            db=db, job_id=req.job_id, candidate_ids=req.candidate_ids, user_id=user_id, weights=req.weights
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching analysis failed: {e!s}")


@router.post("/what-if", response_model=WhatIfSimulationResponse)
def simulate_what_if(req: WhatIfSimulationRequest, db: Session = Depends(get_db)):
    """
    Recruiter What-If Sensitivity Simulator:
    Simulates score and rank shifts when criteria weights or requirements change
    without persisting mutations to candidate profiles or database state.
    """
    try:
        weights_dict = req.weights.model_dump() if req.weights else None
        reqs_list = [r.model_dump() for r in req.modified_requirements] if req.modified_requirements else None

        sim_res = matching_service.simulate_what_if(
            db=db,
            job_id=req.job_id,
            weights=weights_dict,
            modified_requirements=reqs_list,
            min_experience_override=req.min_experience_override,
        )
        return sim_res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-If simulation failed: {e!s}")


@router.get("/results/{job_id}", response_model=list[MatchingAnalysisResponse])
def get_results(job_id: str, db: Session = Depends(get_db)):
    return matching_service.get_rankings(db, job_id=job_id)


@router.get("/analysis/{analysis_id}", response_model=MatchingAnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = matching_service.get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/rankings/{job_id}", response_model=list[MatchingAnalysisResponse])
def get_rankings(
    job_id: str,
    sort_by: str = Query("overall_score"),
    sort_order: str = Query("desc"),
    min_score: float | None = None,
    db: Session = Depends(get_db),
):
    return matching_service.get_rankings(
        db=db, job_id=job_id, sort_by=sort_by, sort_order=sort_order, min_score=min_score
    )


@router.get("/candidate/{candidate_id}/recommend-jobs")
def recommend_jobs_for_candidate(
    candidate_id: str, exclude_job_id: str | None = Query(None), db: Session = Depends(get_db)
):
    """
    AI Candidate Recommendations:
    Scans active requisitions and recommends other suitable job openings for this candidate
    based on skill overlap and chronological experience.
    """
    from app.models.all_models import Candidate, Job

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    cand_skills = {s.skill_name.lower().strip() for s in candidate.skills}
    other_jobs_query = db.query(Job)
    if exclude_job_id:
        other_jobs_query = other_jobs_query.filter(Job.id != exclude_job_id)
    other_jobs = other_jobs_query.limit(25).all()

    recommendations = []
    for j in other_jobs:
        req_skills = [r.skill_name.strip() for r in j.requirements]
        matched = [s for s in req_skills if s.lower() in cand_skills]
        missing = [s for s in req_skills if s.lower() not in cand_skills]

        skill_pct = (len(matched) / len(req_skills)) * 100.0 if req_skills else 50.0
        exp_pct = (
            min(100.0, (candidate.total_experience_years / max(j.min_experience, 1.0)) * 100.0)
            if j.min_experience > 0
            else 90.0
        )
        est_score = round((skill_pct * 0.7) + (exp_pct * 0.3), 1)

        recommendations.append(
            {
                "job_id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "min_experience": j.min_experience,
                "fit_score": est_score,
                "matched_skills": matched,
                "missing_skills": missing[:4],
                "recommendation_reason": (
                    f"Candidate matches {len(matched)} of {len(req_skills)} required competencies"
                    + (f" ({', '.join(matched[:3])})" if matched else "")
                    + f" with {candidate.total_experience_years} years relevant experience."
                ),
            }
        )

    recommendations.sort(key=lambda x: x["fit_score"], reverse=True)
    return recommendations[:5]

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_current_user
from app.models.all_models import User
from app.schemas.all_schemas import (
    MatchRequest,
    MatchingAnalysisResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse
)
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/matching", tags=["AI Matching"])
matching_service = MatchingService()


@router.post("/analyze", response_model=List[MatchingAnalysisResponse])
def analyze_match(
    req: MatchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        results = matching_service.analyze_match(
            db=db,
            job_id=req.job_id,
            candidate_ids=req.candidate_ids,
            user_id=user_id,
            weights=req.weights
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching analysis failed: {str(e)}")


@router.post("/what-if", response_model=WhatIfSimulationResponse)
def simulate_what_if(
    req: WhatIfSimulationRequest,
    db: Session = Depends(get_db)
):
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
            min_experience_override=req.min_experience_override
        )
        return sim_res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-If simulation failed: {str(e)}")


@router.get("/results/{job_id}", response_model=List[MatchingAnalysisResponse])
def get_results(job_id: str, db: Session = Depends(get_db)):
    return matching_service.get_rankings(db, job_id=job_id)


@router.get("/analysis/{analysis_id}", response_model=MatchingAnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = matching_service.get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/rankings/{job_id}", response_model=List[MatchingAnalysisResponse])
def get_rankings(
    job_id: str,
    sort_by: str = Query("overall_score"),
    sort_order: str = Query("desc"),
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    return matching_service.get_rankings(
        db=db,
        job_id=job_id,
        sort_by=sort_by,
        sort_order=sort_order,
        min_score=min_score
    )

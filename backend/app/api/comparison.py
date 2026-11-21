from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.all_schemas import CompareRequest, ComparisonResponse
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/comparison", tags=["Candidate Comparison"])
comp_service = ComparisonService()


@router.post("/compare", response_model=ComparisonResponse)
def compare_candidates(req: CompareRequest, db: Session = Depends(get_db)):
    if len(req.candidate_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 candidates to compare.")

    try:
        result = comp_service.compare_candidates(
            db=db,
            job_id=req.job_id,
            candidate_ids=req.candidate_ids
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

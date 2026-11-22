import os
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user
from app.models.all_models import User
from app.schemas.all_schemas import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobRequirementResponse,
    JobRequirementCreate,
    CriteriaApprovalRequest,
    PaginatedResponse
)
from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.docx_parser import extract_text_from_docx
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])
job_service = JobService()


@router.get("", response_model=PaginatedResponse[JobResponse])
def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    jobs, total = job_service.get_jobs(db, skip=skip, limit=limit, search=search, status=status)
    return {
        "items": jobs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=JobResponse)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    return job_service.create_job(db, job_in, user_id=user_id)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    job_in: JobUpdate,
    db: Session = Depends(get_db)
):
    job = job_service.update_job(db, job_id, job_in)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    success = job_service.delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/extract-requirements", response_model=List[JobRequirementResponse])
def extract_requirements(job_id: str, db: Session = Depends(get_db)):
    reqs = job_service.extract_requirements(db, job_id)
    return reqs


@router.put("/{job_id}/requirements", response_model=List[JobRequirementResponse])
def update_requirements(
    job_id: str,
    requirements: List[JobRequirementCreate],
    db: Session = Depends(get_db)
):
    job_in = JobUpdate(requirements=requirements)
    job = job_service.update_job(db, job_id, job_in)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.requirements


@router.post("/{job_id}/approve-criteria", response_model=JobResponse)
def approve_criteria(
    job_id: str,
    approval_in: CriteriaApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Recruiter Criteria Approval Workflow:
    Review, edit and approve extracted job criteria and scoring weights
    before launching resume screening.
    """
    weights_dict = approval_in.scoring_weights.model_dump() if approval_in.scoring_weights else None
    job = job_service.approve_criteria(
        db=db,
        job_id=job_id,
        requirements=approval_in.requirements,
        scoring_weights=weights_dict
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/upload-jd")
async def upload_job_document(file: UploadFile = File(...)):
    """Upload JD document (PDF, DOCX, TXT) and extract structured requirements."""
    ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if ext not in ["pdf", "docx", "doc", "txt"]:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, or TXT job documents are supported.")

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        extracted_text = ""
        error_msg = None
        if ext == "pdf":
            res = extract_text_from_pdf(tmp_path)
            extracted_text = res.get("text", "")
            error_msg = res.get("error")
        elif ext in ["docx", "doc"]:
            res = extract_text_from_docx(tmp_path)
            extracted_text = res.get("text", "")
            error_msg = res.get("error")
        elif ext == "txt":
            extracted_text = content.decode("utf-8", errors="ignore")

        if error_msg or not extracted_text.strip():
            raise HTTPException(status_code=400, detail=error_msg or "Empty or unreadable document.")

        parsed = job_service.parse_job_document(extracted_text, filename=file.filename)
        return parsed
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


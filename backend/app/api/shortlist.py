from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_current_user
from app.models.all_models import User, Shortlist
from app.schemas.all_schemas import (
    ShortlistCreate,
    ShortlistUpdateStatus,
    ShortlistResponse,
    RecruiterNoteCreate,
    RecruiterNoteResponse
)
from app.services.shortlist_service import ShortlistService

router = APIRouter(prefix="/shortlist", tags=["Shortlisting & Recruiter Notes"])
shortlist_service = ShortlistService()


@router.post("", response_model=ShortlistResponse)
def add_to_shortlist(
    req: ShortlistCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    return shortlist_service.add_to_shortlist(
        db=db,
        job_id=req.job_id,
        candidate_id=req.candidate_id,
        user_id=user_id,
        comments=req.comments
    )


@router.post("/{job_id}/{candidate_id}", response_model=ShortlistResponse)
def add_to_shortlist_by_ids(
    job_id: str,
    candidate_id: str,
    comments: Optional[str] = Query(""),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    return shortlist_service.add_to_shortlist(
        db=db,
        job_id=job_id,
        candidate_id=candidate_id,
        user_id=user_id,
        comments=comments
    )


@router.get("/status/{job_id}/{candidate_id}")
def get_shortlist_status(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(Shortlist).filter(
        Shortlist.job_id == job_id,
        Shortlist.candidate_id == candidate_id
    ).first()
    return {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "is_shortlisted": record is not None and record.status == "shortlisted",
        "status": record.status if record else None,
        "shortlist_id": record.id if record else None
    }


@router.post("/{job_id}/{candidate_id}/notes", response_model=RecruiterNoteResponse)
def add_note_by_ids(
    job_id: str,
    candidate_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    content = body.get("note") or body.get("content") or ""
    return shortlist_service.add_note(
        db=db,
        candidate_id=candidate_id,
        content=content,
        job_id=job_id,
        user_id=user_id
    )


@router.delete("/{job_id}/{candidate_id}")
def remove_from_shortlist_by_ids(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(Shortlist).filter(
        Shortlist.job_id == job_id,
        Shortlist.candidate_id == candidate_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Shortlist record not found")
    shortlist_service.remove_from_shortlist(db, record.id)
    return {"message": "Candidate removed from shortlist"}


@router.delete("/{shortlist_id}")
def remove_from_shortlist(shortlist_id: str, db: Session = Depends(get_db)):
    success = shortlist_service.remove_from_shortlist(db, shortlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shortlist record not found")
    return {"message": "Candidate removed from shortlist"}


@router.get("/job/{job_id}", response_model=List[ShortlistResponse])
def get_job_shortlists(job_id: str, db: Session = Depends(get_db)):
    return shortlist_service.get_job_shortlists(db, job_id)


@router.put("/{shortlist_id}/status", response_model=ShortlistResponse)
def update_status(
    shortlist_id: str,
    req: ShortlistUpdateStatus,
    db: Session = Depends(get_db)
):
    res = shortlist_service.update_shortlist_status(db, shortlist_id, req.status)
    if not res:
        raise HTTPException(status_code=404, detail="Shortlist record not found")
    return res


@router.post("/notes", response_model=RecruiterNoteResponse)
def add_note(
    req: RecruiterNoteCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    return shortlist_service.add_note(
        db=db,
        candidate_id=req.candidate_id,
        content=req.content,
        job_id=req.job_id,
        user_id=user_id
    )


@router.get("/notes/{candidate_id}", response_model=List[RecruiterNoteResponse])
def get_notes(
    candidate_id: str,
    job_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return shortlist_service.get_notes(db, candidate_id=candidate_id, job_id=job_id)

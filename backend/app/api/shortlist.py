from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user
from app.models.all_models import Shortlist, User
from app.schemas.all_schemas import (
    RecruiterNoteCreate,
    RecruiterNoteResponse,
    ShortlistCreate,
    ShortlistResponse,
    ShortlistUpdateStatus,
)
from app.services.shortlist_service import ShortlistService

router = APIRouter(prefix="/shortlist", tags=["Shortlisting & Recruiter Notes"])
shortlist_service = ShortlistService()


@router.post("", response_model=ShortlistResponse)
def add_to_shortlist(
    req: ShortlistCreate, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    return shortlist_service.add_to_shortlist(
        db=db, job_id=req.job_id, candidate_id=req.candidate_id, user_id=user_id, comments=req.comments
    )


@router.post("/{job_id}/{candidate_id}", response_model=ShortlistResponse)
def add_to_shortlist_by_ids(
    job_id: str,
    candidate_id: str,
    comments: str | None = Query(""),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    return shortlist_service.add_to_shortlist(
        db=db, job_id=job_id, candidate_id=candidate_id, user_id=user_id, comments=comments
    )


@router.get("/status/{job_id}/{candidate_id}")
def get_shortlist_status(job_id: str, candidate_id: str, db: Session = Depends(get_db)):
    record = db.query(Shortlist).filter(Shortlist.job_id == job_id, Shortlist.candidate_id == candidate_id).first()
    return {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "is_shortlisted": record is not None and record.status == "shortlisted",
        "status": record.status if record else None,
        "shortlist_id": record.id if record else None,
    }


@router.post("/{job_id}/{candidate_id}/notes", response_model=RecruiterNoteResponse)
def add_note_by_ids(
    job_id: str,
    candidate_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    content = body.get("note") or body.get("content") or ""
    return shortlist_service.add_note(db=db, candidate_id=candidate_id, content=content, job_id=job_id, user_id=user_id)


@router.delete("/{job_id}/{candidate_id}")
def remove_from_shortlist_by_ids(
    job_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    query = db.query(Shortlist).filter(Shortlist.job_id == job_id, Shortlist.candidate_id == candidate_id)
    if current_user and current_user.role not in ("admin", "super_admin"):
        query = query.filter((Shortlist.user_id == current_user.id) | (Shortlist.user_id.is_(None)))
    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="Shortlist record not found or access denied")
    shortlist_service.remove_from_shortlist(
        db,
        record.id,
        user_id=current_user.id if current_user else None,
        is_admin=(current_user.role in ("admin", "super_admin") if current_user else False),
    )
    return {"message": "Candidate removed from shortlist"}


@router.delete("/{shortlist_id}")
def remove_from_shortlist(
    shortlist_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    is_admin = current_user.role in ("admin", "super_admin") if current_user else False
    success = shortlist_service.remove_from_shortlist(db, shortlist_id, user_id=user_id, is_admin=is_admin)
    if not success:
        raise HTTPException(status_code=404, detail="Shortlist record not found or access denied")
    return {"message": "Candidate removed from shortlist"}


@router.get("/job/{job_id}", response_model=list[ShortlistResponse])
def get_job_shortlists(
    job_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return shortlist_service.get_job_shortlists(db, job_id, skip=skip, limit=limit)


@router.put("/{shortlist_id}/status", response_model=ShortlistResponse)
def update_status(shortlist_id: str, req: ShortlistUpdateStatus, db: Session = Depends(get_db)):
    res = shortlist_service.update_shortlist_status(db, shortlist_id, req.status)
    if not res:
        raise HTTPException(status_code=404, detail="Shortlist record not found")
    return res


@router.post("/notes", response_model=RecruiterNoteResponse)
def add_note(
    req: RecruiterNoteCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    return shortlist_service.add_note(
        db=db, candidate_id=req.candidate_id, content=req.content, job_id=req.job_id, user_id=user_id
    )


@router.get("/notes/{candidate_id}", response_model=list[RecruiterNoteResponse])
def get_notes(
    candidate_id: str,
    job_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return shortlist_service.get_notes(db, candidate_id=candidate_id, job_id=job_id, skip=skip, limit=limit)

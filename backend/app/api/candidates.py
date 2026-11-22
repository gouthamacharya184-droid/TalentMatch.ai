from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user
from app.models.all_models import User
from app.schemas.all_schemas import (
    CandidateCreate,
    CandidateResponse,
    CandidateSkillResponse,
    CandidateUpdate,
    PaginatedResponse,
)
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidates", tags=["Candidates"])
cand_service = CandidateService()


@router.post("", response_model=CandidateResponse)
def create_candidate(
    cand_in: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    return cand_service.create_candidate(db, cand_in, user_id=user_id)


@router.get("", response_model=PaginatedResponse[CandidateResponse])
def get_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    min_experience: float | None = None,
    max_experience: float | None = None,
    skill: str | None = None,
    db: Session = Depends(get_db),
):
    candidates, total = cand_service.get_candidates(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        min_experience=min_experience,
        max_experience=max_experience,
        skill=skill,
    )
    return {"items": candidates, "total": total, "skip": skip, "limit": limit}


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    cand = cand_service.get_candidate(db, candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(candidate_id: str, cand_in: CandidateUpdate, db: Session = Depends(get_db)):
    cand = cand_service.update_candidate(db, candidate_id, cand_in)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    success = cand_service.delete_candidate(db, candidate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully"}


@router.get("/{candidate_id}/skills", response_model=list[CandidateSkillResponse])
def get_candidate_skills(candidate_id: str, db: Session = Depends(get_db)):
    return cand_service.get_candidate_skills(db, candidate_id)


@router.get("/{candidate_id}/evidence", response_model=list[dict])
def get_candidate_evidence(candidate_id: str, db: Session = Depends(get_db)):
    """Retrieve all traceable evidence references with page citations for this candidate."""
    from app.models.all_models import EvidenceReference

    cand = cand_service.get_candidate(db, candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    items = db.query(EvidenceReference).filter(EvidenceReference.candidate_id == candidate_id).all()
    if items:
        return [
            {
                "id": ev.id,
                "candidate_id": ev.candidate_id,
                "resume_id": ev.resume_id,
                "job_id": ev.job_id,
                "criterion": ev.criterion,
                "criterion_type": ev.criterion_type,
                "snippet": ev.snippet,
                "page_number": ev.page_number,
                "confidence": ev.confidence,
                "evidence_classification": ev.evidence_classification,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
            }
            for ev in items
        ]

    # Dynamic fallback generation from candidate skills & resume if not yet indexed
    dyn_evidence = []
    resume = cand.resume
    full_text = (resume.raw_text if resume else "") or ""
    page_texts = resume.page_texts if resume and resume.page_texts else {"1": full_text}

    for s in cand.skills:
        skill_lower = s.skill_name.lower()
        found_page = 1
        snippet = f"Technical skill '{s.skill_name}' recorded in candidate profile."
        ev_class = s.evidence_type if hasattr(s, "evidence_type") and s.evidence_type else "explicit"

        for p_num, p_text in page_texts.items():
            idx = p_text.lower().find(skill_lower)
            if idx != -1:
                found_page = int(p_num) if p_num.isdigit() else 1
                start = max(0, idx - 40)
                end = min(len(p_text), idx + len(skill_lower) + 60)
                snippet = p_text[start:end].replace("\n", " ").strip()
                break

        dyn_evidence.append(
            {
                "id": f"dyn_{s.id}",
                "candidate_id": cand.id,
                "resume_id": resume.id if resume else None,
                "job_id": None,
                "criterion": s.skill_name,
                "criterion_type": "skill",
                "snippet": snippet,
                "page_number": found_page,
                "confidence": 0.95,
                "evidence_classification": ev_class,
                "created_at": cand.created_at.isoformat() if cand.created_at else None,
            }
        )

    return dyn_evidence

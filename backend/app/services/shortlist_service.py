from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.all_models import Shortlist, RecruiterNote, Candidate
from app.services.notification_service import NotificationService


class ShortlistService:
    def add_to_shortlist(
        self,
        db: Session,
        job_id: str,
        candidate_id: str,
        user_id: Optional[str] = None,
        comments: Optional[str] = ""
    ) -> Shortlist:
        existing = db.query(Shortlist).filter(
            Shortlist.job_id == job_id,
            Shortlist.candidate_id == candidate_id
        ).first()

        if existing:
            existing.comments = comments or existing.comments
            existing.status = "shortlisted"
            db.commit()
            db.refresh(existing)
            return existing

        shortlist = Shortlist(
            job_id=job_id,
            candidate_id=candidate_id,
            user_id=user_id,
            status="shortlisted",
            comments=comments or ""
        )
        db.add(shortlist)

        # Update candidate status
        cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if cand:
            cand.status = "shortlisted"

        db.commit()
        db.refresh(shortlist)

        NotificationService.log_activity(
            db=db,
            action="SHORTLIST_CANDIDATE",
            entity_type="candidate",
            entity_id=candidate_id,
            user_id=user_id,
            details={"job_id": job_id, "status": "shortlisted"}
        )

        return shortlist

    def remove_from_shortlist(self, db: Session, shortlist_id: str) -> bool:
        shortlist = db.query(Shortlist).filter(Shortlist.id == shortlist_id).first()
        if not shortlist:
            return False

        # Reset candidate status if appropriate
        cand = db.query(Candidate).filter(Candidate.id == shortlist.candidate_id).first()
        if cand and cand.status == "shortlisted":
            cand.status = "analyzed"

        db.delete(shortlist)
        db.commit()
        return True

    def get_job_shortlists(self, db: Session, job_id: str) -> List[Shortlist]:
        return db.query(Shortlist).filter(Shortlist.job_id == job_id).all()

    def update_shortlist_status(self, db: Session, shortlist_id: str, status: str) -> Optional[Shortlist]:
        shortlist = db.query(Shortlist).filter(Shortlist.id == shortlist_id).first()
        if not shortlist:
            return None

        shortlist.status = status
        cand = db.query(Candidate).filter(Candidate.id == shortlist.candidate_id).first()
        if cand:
            cand.status = status

        db.commit()
        db.refresh(shortlist)
        return shortlist

    def add_note(
        self,
        db: Session,
        candidate_id: str,
        content: str,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> RecruiterNote:
        clean_job_id = job_id.strip() if (job_id and isinstance(job_id, str) and job_id.strip()) else None
        note = RecruiterNote(
            candidate_id=candidate_id,
            job_id=clean_job_id,
            user_id=user_id,
            content=content
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    def get_notes(
        self,
        db: Session,
        candidate_id: str,
        job_id: Optional[str] = None
    ) -> List[RecruiterNote]:
        query = db.query(RecruiterNote).filter(RecruiterNote.candidate_id == candidate_id)
        clean_job_id = job_id.strip() if (job_id and isinstance(job_id, str) and job_id.strip()) else None
        if clean_job_id:
            query = query.filter(RecruiterNote.job_id == clean_job_id)
        return query.order_by(RecruiterNote.created_at.desc()).all()

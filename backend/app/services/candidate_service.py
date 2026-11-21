import os
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.all_models import Candidate, CandidateSkill, Resume, MatchingAnalysis
from app.schemas.all_schemas import CandidateUpdate, CandidateCreate


class CandidateService:
    def get_candidates(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
        min_experience: Optional[float] = None,
        max_experience: Optional[float] = None,
        skill: Optional[str] = None
    ) -> (List[Candidate], int):
        query = db.query(Candidate)

        if search:
            query = query.filter(
                Candidate.name.ilike(f"%{search}%") |
                Candidate.email.ilike(f"%{search}%") |
                Candidate.location.ilike(f"%{search}%")
            )
        if status:
            query = query.filter(Candidate.status == status)
        if min_experience is not None:
            query = query.filter(Candidate.total_experience_years >= min_experience)
        if max_experience is not None:
            query = query.filter(Candidate.total_experience_years <= max_experience)
        if skill:
            query = query.join(Candidate.skills).filter(CandidateSkill.skill_name.ilike(f"%{skill}%"))

        total = query.count()
        candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()
        return candidates, total

    def get_candidate(self, db: Session, candidate_id: str) -> Optional[Candidate]:
        return db.query(Candidate).filter(Candidate.id == candidate_id).first()

    def update_candidate(
        self,
        db: Session,
        candidate_id: str,
        cand_in: CandidateUpdate
    ) -> Optional[Candidate]:
        candidate = self.get_candidate(db, candidate_id)
        if not candidate:
            return None

        update_data = cand_in.model_dump(exclude_unset=True) if hasattr(cand_in, 'model_dump') else cand_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(candidate, field, value)

        db.commit()
        db.refresh(candidate)
        return candidate

    def create_candidate(
        self,
        db: Session,
        cand_in: CandidateCreate,
        user_id: Optional[str] = None
    ) -> Candidate:
        candidate = Candidate(
            user_id=user_id,
            name=cand_in.name,
            email=cand_in.email,
            phone=cand_in.phone,
            location=cand_in.location,
            education=cand_in.education,
            total_experience_years=cand_in.total_experience_years,
            extracted_profile=cand_in.extracted_profile,
            status=cand_in.status or "new"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        if cand_in.skills:
            for s_name in cand_in.skills:
                skill = CandidateSkill(
                    candidate_id=candidate.id,
                    skill_name=s_name,
                    proficiency_level="intermediate",
                    source="manual"
                )
                db.add(skill)
            db.commit()
            db.refresh(candidate)

        return candidate

    def delete_candidate(self, db: Session, candidate_id: str) -> bool:
        candidate = self.get_candidate(db, candidate_id)
        if not candidate:
            return False

        # If resume exists, delete file from storage safely
        if candidate.resume and candidate.resume.file_path:
            try:
                if os.path.exists(candidate.resume.file_path):
                    os.remove(candidate.resume.file_path)
            except Exception:
                pass

        db.delete(candidate)
        db.commit()
        return True

    def get_candidate_skills(self, db: Session, candidate_id: str) -> List[CandidateSkill]:
        return db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate_id).all()

import logging
import os
import re
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.ai_engine.agents.job_agent import JobDescriptionAgent
from app.models.all_models import Job, JobRequirement, utc_now
from app.schemas.all_schemas import JobCreate, JobRequirementCreate, JobUpdate
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self):
        self.job_agent = JobDescriptionAgent()

    def get_jobs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        status: str | None = None,
        campaign_id: str | None = None,
    ) -> tuple[list[Job], int]:
        query = db.query(Job)
        if search:
            query = query.filter(Job.title.ilike(f"%{search}%") | Job.company.ilike(f"%{search}%"))
        if status:
            query = query.filter(Job.status == status)
        if campaign_id:
            query = query.filter(Job.campaign_id == campaign_id)

        total = query.count()
        jobs = (
            query.options(selectinload(Job.requirements))
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs, total

    def get_job(self, db: Session, job_id: str) -> Job | None:
        return db.query(Job).options(selectinload(Job.requirements)).filter(Job.id == job_id).first()

    def create_job(self, db: Session, job_in: JobCreate, user_id: str | None = None) -> Job:
        job = Job(
            user_id=user_id,
            campaign_id=getattr(job_in, "campaign_id", None),
            title=job_in.title,
            company=job_in.company,
            location=job_in.location,
            employment_type=job_in.employment_type,
            min_experience=job_in.min_experience,
            education_req=job_in.education_req,
            description=job_in.description,
            status="active",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # If explicit requirements provided, persist them
        if job_in.requirements:
            for req in job_in.requirements:
                r = JobRequirement(
                    job_id=job.id,
                    skill_name=req.skill_name,
                    category=req.category,
                    skill_type=req.skill_type,
                    weight=1.0 if req.category == "mandatory" else 0.5,
                )
                db.add(r)
        else:
            # Use JobDescriptionAgent to extract structured criteria
            jd_analysis = self.job_agent.execute(
                job_text=job.description, job_title=job.title, company=job.company, db=db, job_id=job.id
            )
            job.extracted_requirements = jd_analysis
            job.scoring_weights = jd_analysis.get("recommended_weights")

            for m in jd_analysis.get("mandatory_skills", []):
                r = JobRequirement(
                    job_id=job.id,
                    skill_name=m["skill_name"],
                    category="mandatory",
                    skill_type=m.get("skill_type", "technical"),
                    weight=m.get("weight", 1.0),
                )
                db.add(r)
            for p in jd_analysis.get("preferred_skills", []):
                r = JobRequirement(
                    job_id=job.id,
                    skill_name=p["skill_name"],
                    category="preferred",
                    skill_type=p.get("skill_type", "technical"),
                    weight=p.get("weight", 0.5),
                )
                db.add(r)

        db.commit()
        db.refresh(job)

        try:
            NotificationService.log_activity(
                db=db,
                action="CREATE_JOB",
                entity_type="job",
                entity_id=job.id,
                user_id=user_id,
                details={"title": job.title, "company": job.company},
            )
        except Exception:
            pass

        return job

    def update_job(self, db: Session, job_id: str, job_in: JobUpdate) -> Job | None:
        job = self.get_job(db, job_id)
        if not job:
            return None

        update_data = (
            job_in.model_dump(exclude_unset=True) if hasattr(job_in, "model_dump") else job_in.dict(exclude_unset=True)
        )
        reqs_data = update_data.pop("requirements", None)

        for field, value in update_data.items():
            setattr(job, field, value)

        if reqs_data is not None:
            db.query(JobRequirement).filter(JobRequirement.job_id == job_id).delete()
            for req in reqs_data:
                r = JobRequirement(
                    job_id=job.id,
                    skill_name=req["skill_name"],
                    category=req.get("category", "mandatory"),
                    skill_type=req.get("skill_type", "technical"),
                    weight=req.get("weight", 1.0 if req.get("category") == "mandatory" else 0.5),
                )
                db.add(r)

        db.commit()
        db.refresh(job)
        return job

    def delete_job(self, db: Session, job_id: str) -> bool:
        job = self.get_job(db, job_id)
        if not job:
            return False
        db.delete(job)
        db.commit()
        return True

    def extract_requirements(self, db: Session, job_id: str) -> list[JobRequirement]:
        job = self.get_job(db, job_id)
        if not job:
            return []

        jd_analysis = self.job_agent.execute(
            job_text=job.description, job_title=job.title, company=job.company, db=db, job_id=job.id
        )

        job.extracted_requirements = jd_analysis
        job.scoring_weights = jd_analysis.get("recommended_weights")
        new_reqs = []

        # Replace existing requirements
        db.query(JobRequirement).filter(JobRequirement.job_id == job_id).delete()

        for m in jd_analysis.get("mandatory_skills", []):
            r = JobRequirement(
                job_id=job.id,
                skill_name=m["skill_name"],
                category="mandatory",
                skill_type=m.get("skill_type", "technical"),
                weight=m.get("weight", 1.0),
            )
            db.add(r)
            new_reqs.append(r)

        for p in jd_analysis.get("preferred_skills", []):
            r = JobRequirement(
                job_id=job.id,
                skill_name=p["skill_name"],
                category="preferred",
                skill_type=p.get("skill_type", "technical"),
                weight=p.get("weight", 0.5),
            )
            db.add(r)
            new_reqs.append(r)

        db.commit()
        return new_reqs

    def approve_criteria(
        self,
        db: Session,
        job_id: str,
        requirements: list[JobRequirementCreate] | None = None,
        scoring_weights: dict[str, float] | None = None,
    ) -> Job | None:
        """Recruiter criteria approval staging checkpoint."""
        job = self.get_job(db, job_id)
        if not job:
            return None

        job.criteria_approved = True
        job.criteria_approved_at = utc_now()
        if scoring_weights:
            job.scoring_weights = scoring_weights

        if requirements:
            db.query(JobRequirement).filter(JobRequirement.job_id == job_id).delete()
            for req in requirements:
                r = JobRequirement(
                    job_id=job.id,
                    skill_name=req.skill_name,
                    category=req.category,
                    skill_type=req.skill_type,
                    weight=1.0 if req.category == "mandatory" else 0.5,
                )
                db.add(r)

        db.commit()
        db.refresh(job)
        return job

    def parse_job_document(self, text: str, filename: str = "") -> dict[str, Any]:
        """Parse raw job description document using JobDescriptionAgent."""
        # 1. Title extraction from text or filename
        title = ""
        title_match = re.search(r"(?:Job Title|Role|Position|Title)\s*:\s*([^|\n\r]+)", text, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        elif filename:
            clean_fn = re.sub(r"^(Job|JD)[_\s-]*", "", os.path.splitext(filename)[0], flags=re.IGNORECASE)
            clean_fn = re.sub(r"([a-z])([A-Z])", r"\1 \2", clean_fn)
            title = clean_fn.replace("_", " ").replace("-", " ").title()
            if "Fullstack" in title or "Full Stack" in title:
                title = title.replace("Fullstack", "Full-Stack").replace("Full Stack", "Full-Stack")

        parsed = self.job_agent.execute(job_text=text, job_title=title or None, db=None)
        final_title = title or parsed.get("title") or "Software Engineer"

        # Format for frontend ingestion form
        all_reqs = []
        for m in parsed.get("mandatory_skills", []):
            all_reqs.append(m)
        for p in parsed.get("preferred_skills", []):
            all_reqs.append(p)

        return {
            "title": final_title,
            "company": "AVOM Consultants",
            "location": "Remote",
            "employment_type": "Full-time",
            "min_experience": parsed.get("min_experience", 3.0),
            "education_req": parsed.get("education_req", "Bachelor's Degree in Computer Science or related"),
            "description": text,
            "requirements": all_reqs,
            "seniority": parsed.get("seniority", "Mid-Level"),
            "responsibilities": parsed.get("responsibilities", []),
            "ambiguities_or_conflicts": parsed.get("ambiguities_or_conflicts", []),
            "recommended_weights": parsed.get("recommended_weights"),
        }

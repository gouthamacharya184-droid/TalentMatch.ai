from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.all_models import (
    ActivityLog,
    Candidate,
    CandidateSkill,
    Job,
    MatchingAnalysis,
    Resume,
    Shortlist,
)


class AnalyticsService:
    def get_dashboard_stats(self, db: Session) -> dict[str, Any]:
        total_jobs = db.query(Job).count()
        total_resumes = db.query(Resume).count()
        total_candidates = db.query(Candidate).count()

        avg_score_res = db.query(func.avg(MatchingAnalysis.overall_score)).scalar()
        avg_matching_score = round(float(avg_score_res), 1) if avg_score_res else 0.0

        total_shortlisted = db.query(Shortlist).filter(Shortlist.status == "shortlisted").count()
        under_review = db.query(Candidate).filter(Candidate.status == "under_review").count()

        recent_jobs = db.query(Job).order_by(Job.created_at.desc()).limit(5).all()
        top_candidates = db.query(MatchingAnalysis).order_by(MatchingAnalysis.overall_score.desc()).limit(5).all()

        # Score distribution
        all_scores = [a.overall_score for a in db.query(MatchingAnalysis.overall_score).all()]
        score_dist = {
            "90-100": sum(1 for s in all_scores if 90 <= s <= 100),
            "80-89": sum(1 for s in all_scores if 80 <= s < 90),
            "70-79": sum(1 for s in all_scores if 70 <= s < 80),
            "60-69": sum(1 for s in all_scores if 60 <= s < 70),
            "Below 60": sum(1 for s in all_scores if s < 60),
        }

        # Top skills availability across candidates
        skill_counts = (
            db.query(CandidateSkill.skill_name, func.count(CandidateSkill.id))
            .group_by(CandidateSkill.skill_name)
            .order_by(func.count(CandidateSkill.id).desc())
            .limit(10)
            .all()
        )
        skills_avail = {name: count for name, count in skill_counts}

        # Recent activity
        activity = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(8).all()

        return {
            "total_jobs": total_jobs,
            "total_resumes": total_resumes,
            "total_candidates": total_candidates,
            "avg_matching_score": avg_matching_score,
            "total_shortlisted": total_shortlisted,
            "under_review": under_review,
            "recent_jobs": recent_jobs,
            "top_candidates": top_candidates,
            "score_distribution": score_dist,
            "skills_availability": skills_avail,
            "recent_activity": activity,
        }

    def get_job_report_data(self, db: Session, job_id: str) -> dict[str, Any]:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        analyses = (
            db.query(MatchingAnalysis)
            .filter(MatchingAnalysis.job_id == job_id)
            .order_by(MatchingAnalysis.overall_score.desc())
            .all()
        )

        return {"job": job, "analyses": analyses, "generated_at": datetime.now(UTC).isoformat()}

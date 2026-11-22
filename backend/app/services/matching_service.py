import logging
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.ai_engine.agents.interview_agent import InterviewIntelligenceAgent
from app.ai_engine.agents.matching_agent import CandidateMatchingAgent
from app.models.all_models import (
    Candidate,
    EvaluationRun,
    Job,
    MatchingAnalysis,
    ScoreBreakdown,
    generate_uuid,
    utc_now,
)

logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self):
        self.matching_agent = CandidateMatchingAgent()
        self.interview_agent = InterviewIntelligenceAgent()

    def analyze_match(
        self,
        db: Session,
        job_id: str,
        candidate_ids: list[str] | None = None,
        user_id: str | None = None,
        weights: dict[str, float] | None = None,
        use_llm: bool = True,
    ) -> list[MatchingAnalysis]:
        """
        Execute AI multi-criteria matching for candidates against job_id.
        If candidate_ids is None or empty, analyzes all existing candidates.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found with id: {job_id}")

        # Use passed weights or job's stored weights or default
        active_weights = weights or job.scoring_weights or self.matching_agent.DEFAULT_WEIGHTS

        job_data = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "min_experience": job.min_experience,
            "education_req": job.education_req,
            "requirements": [
                {
                    "skill_name": r.skill_name,
                    "category": r.category,
                    "skill_type": r.skill_type,
                    "weight": r.weight if hasattr(r, "weight") else 1.0,
                }
                for r in job.requirements
            ],
        }

        query = db.query(Candidate)
        if candidate_ids:
            query = query.filter(Candidate.id.in_(candidate_ids))
        candidates = query.all()

        analyses = []

        # Create or update an EvaluationRun entry
        eval_run = EvaluationRun(
            id=generate_uuid(),
            job_id=job.id,
            user_id=user_id,
            run_name=f"Evaluation Run for {job.title}",
            weights_snapshot=active_weights,
            criteria_snapshot=[{"skill": r.skill_name, "category": r.category} for r in job.requirements],
            candidate_count=len(candidates),
            created_at=utc_now(),
        )
        db.add(eval_run)
        db.flush()

        for candidate in candidates:
            # Delete any prior analysis for this job & candidate pair to prevent duplicates
            db.query(MatchingAnalysis).filter(
                MatchingAnalysis.job_id == job_id, MatchingAnalysis.candidate_id == candidate.id
            ).delete()

            cand_skills = [
                {
                    "skill_name": s.skill_name,
                    "proficiency_level": s.proficiency_level,
                    "evidence_type": s.evidence_type if hasattr(s, "evidence_type") else "explicit",
                }
                for s in candidate.skills
            ]
            resume_text = candidate.resume.raw_text if candidate.resume and candidate.resume.raw_text else ""
            page_texts = candidate.resume.page_texts if candidate.resume and candidate.resume.page_texts else {}

            cand_dict = {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "total_experience_years": candidate.total_experience_years,
                "education": candidate.education or [],
                "projects": candidate.projects
                or (candidate.extracted_profile.get("projects", []) if candidate.extracted_profile else []),
                "experience": candidate.extracted_profile.get("experience", []) if candidate.extracted_profile else [],
                "skills": cand_skills,
                "raw_text": resume_text,
                "page_texts": page_texts,
            }

            match_result = self.matching_agent.evaluate_match(
                job_data=job_data, candidate_data=cand_dict, weights=active_weights, db=db, candidate_id=candidate.id
            )

            analysis = MatchingAnalysis(
                id=generate_uuid(),
                job_id=job.id,
                candidate_id=candidate.id,
                user_id=user_id,
                evaluation_run_id=eval_run.id,
                overall_score=match_result["overall_score"],
                technical_score=match_result["technical_score"],
                projects_score=match_result["projects_score"],
                experience_score=match_result["experience_score"],
                preferred_score=match_result["preferred_score"],
                education_score=match_result["education_score"],
                semantic_score=match_result["semantic_score"],
                weights_used=match_result["weights_used"],
                confidence_score=match_result["confidence_score"],
                uncertainty_notes=match_result["uncertainty_notes"],
                explanation=match_result["explanation"],
                strengths=match_result["strengths"],
                skill_gaps=match_result["skill_gaps"],
                matched_skills=match_result["matched_skills"],
                missing_skills=match_result["missing_skills"],
                related_skills=match_result["related_skills"],
                created_at=utc_now(),
            )
            db.add(analysis)
            db.flush()

            # Create detailed ScoreBreakdown items
            components_map = [
                (
                    "Required Skills",
                    match_result["technical_score"],
                    100.0,
                    active_weights.get("required_skills", 35.0),
                ),
                (
                    "Projects & Implementation",
                    match_result["projects_score"],
                    100.0,
                    active_weights.get("projects", 25.0),
                ),
                (
                    "Professional Experience",
                    match_result["experience_score"],
                    100.0,
                    active_weights.get("experience", 15.0),
                ),
                (
                    "Preferred Skills",
                    match_result["preferred_score"],
                    100.0,
                    active_weights.get("preferred_skills", 15.0),
                ),
                (
                    "Education & Certifications",
                    match_result["education_score"],
                    100.0,
                    active_weights.get("education", 10.0),
                ),
            ]
            for comp_name, score_val, max_val, wt_pct in components_map:
                sb = ScoreBreakdown(
                    analysis_id=analysis.id,
                    component=comp_name,
                    score=score_val,
                    max_score=max_val,
                    weight_percentage=wt_pct,
                    details={"score": score_val, "weight": wt_pct},
                )
                db.add(sb)

            analyses.append(analysis)

        # Update average score on evaluation run
        if analyses:
            eval_run.average_score = round(sum(a.overall_score for a in analyses) / len(analyses), 1)

        db.commit()

        # Update candidate status
        for a in analyses:
            db.refresh(a)
            cand = db.query(Candidate).filter(Candidate.id == a.candidate_id).first()
            if cand and cand.status == "new":
                cand.status = "analyzed"
        db.commit()

        return analyses

    def get_analysis(self, db: Session, analysis_id: str) -> MatchingAnalysis | None:
        return db.query(MatchingAnalysis).filter(MatchingAnalysis.id == analysis_id).first()

    def get_rankings(
        self,
        db: Session,
        job_id: str,
        sort_by: str = "overall_score",
        sort_order: str = "desc",
        min_score: float | None = None,
    ) -> list[MatchingAnalysis]:
        query = db.query(MatchingAnalysis).options(
            selectinload(MatchingAnalysis.candidate),
            selectinload(MatchingAnalysis.job),
        ).filter(MatchingAnalysis.job_id == job_id)
        if min_score is not None:
            query = query.filter(MatchingAnalysis.overall_score >= min_score)

        col = getattr(MatchingAnalysis, sort_by, MatchingAnalysis.overall_score)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(col))
        else:
            query = query.order_by(col)

        return query.all()

    def simulate_what_if(
        self,
        db: Session,
        job_id: str,
        weights: dict[str, float] | None = None,
        modified_requirements: list[dict[str, Any]] | None = None,
        min_experience_override: float | None = None,
    ) -> dict[str, Any]:
        """Simulate criteria or weight adjustments without altering persisted records."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found with id: {job_id}")

        analyses = (
            db.query(MatchingAnalysis)
            .options(selectinload(MatchingAnalysis.candidate).selectinload(Candidate.skills))
            .filter(MatchingAnalysis.job_id == job_id)
            .all()
        )
        if not analyses:
            # If not yet analyzed, run base analysis
            analyses = self.analyze_match(db, job_id=job_id)

        candidate_eval_data = []
        for a in analyses:
            cand = a.candidate
            if not cand:
                cand = db.query(Candidate).filter(Candidate.id == a.candidate_id).first()
            if cand:
                candidate_eval_data.append(
                    {
                        "candidate_id": cand.id,
                        "name": cand.name,
                        "previous_score": a.overall_score,
                        "technical_score": a.technical_score,
                        "projects_score": a.projects_score,
                        "experience_score": a.experience_score,
                        "preferred_score": a.preferred_score,
                        "education_score": a.education_score,
                        "skills": [s.skill_name for s in cand.skills],
                    }
                )

        job_dict = {
            "id": job.id,
            "title": job.title,
            "min_experience": min_experience_override if min_experience_override is not None else job.min_experience,
        }

        return self.matching_agent.simulate_what_if(
            job_data=job_dict,
            candidate_evaluations=candidate_eval_data,
            new_weights=weights,
            modified_requirements=modified_requirements,
        )

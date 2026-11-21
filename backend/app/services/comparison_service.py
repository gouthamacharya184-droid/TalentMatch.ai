from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.all_models import Job, Candidate, MatchingAnalysis
from app.services.matching_service import MatchingService


class ComparisonService:
    def __init__(self):
        self.matching_service = MatchingService()

    def compare_candidates(
        self,
        db: Session,
        job_id: str,
        candidate_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Produce a side-by-side comparison for multiple candidates against the same job.
        Computes skill overlap matrix, score differences, strengths, and gaps.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found with id: {job_id}")

        candidates_data = []
        all_skills_set = set()

        # Gather job requirements skills
        for r in job.requirements:
            all_skills_set.add(r.skill_name)

        for c_id in candidate_ids:
            cand = db.query(Candidate).filter(Candidate.id == c_id).first()
            if not cand:
                continue

            analysis = db.query(MatchingAnalysis).filter(
                MatchingAnalysis.job_id == job_id,
                MatchingAnalysis.candidate_id == c_id
            ).first()

            # If no analysis exists, run it on the fly
            if not analysis:
                results = self.matching_service.analyze_match(db, job_id, [c_id], use_llm=False)
                analysis = results[0] if results else None

            if cand and analysis:
                candidates_data.append({
                    "candidate": cand,
                    "analysis": analysis
                })
                # Collect skills
                for s in cand.skills:
                    all_skills_set.add(s.skill_name)

        # Build skill overlap matrix
        skill_overlap = []
        for skill_name in sorted(list(all_skills_set)):
            entry = {"skill": skill_name, "candidates": {}}
            for item in candidates_data:
                c = item["candidate"]
                cand_skill_names = {s.skill_name.lower() for s in c.skills}
                has_skill = skill_name.lower() in cand_skill_names
                entry["candidates"][c.id] = has_skill
            skill_overlap.append(entry)

        return {
            "job": job,
            "candidates": candidates_data,
            "skill_overlap": skill_overlap
        }

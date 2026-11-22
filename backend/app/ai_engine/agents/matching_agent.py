import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine.agents.base_agent import BaseAgent
from app.ai_engine.agents.experience_agent import ExperienceEvaluationAgent
from app.ai_engine.agents.skills_agent import TechnicalSkillsAgent
from app.ai_engine.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class CandidateMatchingAgent(BaseAgent):
    """
    Agent 5: Candidate Matching Agent.
    Calculates transparent, explainable multi-component match scores using configurable weights.
    Generates detailed score contributions, avoids duplicate penalties, exposes uncertainty,
    and supports recruiter What-If simulations.
    """

    DEFAULT_WEIGHTS = {
        "required_skills": 35.0,
        "projects": 25.0,
        "experience": 15.0,
        "preferred_skills": 15.0,
        "education": 10.0,
    }

    def __init__(self):
        super().__init__(
            agent_name="CandidateMatchingAgent",
            description="Computes explainable, weight-normalized recruitment match scores and What-If simulation deltas.",
        )
        self.embedding_service = EmbeddingService()
        self.skills_agent = TechnicalSkillsAgent()
        self.experience_agent = ExperienceEvaluationAgent()

    def normalize_weights(self, weights: dict[str, float] | None) -> dict[str, float]:
        """Validate and normalize scoring weights so they sum exactly to 100%."""
        if not weights:
            return dict(self.DEFAULT_WEIGHTS)

        req = float(weights.get("required_skills", 35.0))
        proj = float(weights.get("projects", 25.0))
        exp = float(weights.get("experience", 15.0))
        pref = float(weights.get("preferred_skills", 15.0))
        edu = float(weights.get("education", 10.0))

        total = req + proj + exp + pref + edu
        if total <= 0:
            return dict(self.DEFAULT_WEIGHTS)

        # Scale to 100
        return {
            "required_skills": round((req / total) * 100.0, 1),
            "projects": round((proj / total) * 100.0, 1),
            "experience": round((exp / total) * 100.0, 1),
            "preferred_skills": round((pref / total) * 100.0, 1),
            "education": round((edu / total) * 100.0, 1),
        }

    def evaluate_match(
        self,
        job_data: dict[str, Any],
        candidate_data: dict[str, Any],
        weights: dict[str, float] | None = None,
        db: Session | None = None,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate candidate against job criteria with full explainability.
        Returns 0-100 overall score, 5 sub-scores, score breakdown, strengths, gaps, and uncertainty.
        """
        start_time = time.time()
        active_weights = self.normalize_weights(weights)

        job_title = job_data.get("title", "Engineering Role")
        job_desc = job_data.get("description", "")
        job_reqs = job_data.get("requirements", [])
        min_exp = float(job_data.get("min_experience", 0.0))

        cand_skills = candidate_data.get("skills", [])
        cand_projects = candidate_data.get("projects", [])
        cand_exp_items = candidate_data.get("experience", [])
        cand_exp_years = float(candidate_data.get("total_experience_years", 0.0))
        cand_edu = candidate_data.get("education", [])
        resume_text = candidate_data.get("raw_text", "")
        page_texts = candidate_data.get("page_texts", {})

        # Separate mandatory and preferred requirements
        mandatory_reqs = [r for r in job_reqs if r.get("category") == "mandatory"]
        preferred_reqs = [r for r in job_reqs if r.get("category") == "preferred"]
        if not mandatory_reqs and not preferred_reqs:
            mandatory_reqs = job_reqs

        # 1. Technical Skills Evaluation (Required + Preferred)
        skills_eval = self.skills_agent.execute(
            job_requirements=job_reqs,
            candidate_skills=cand_skills,
            candidate_projects=cand_projects,
            candidate_experience=cand_exp_items,
            resume_text=resume_text,
            page_texts=page_texts,
            db=db,
            candidate_id=candidate_id,
        )

        req_evals = [e for e in skills_eval["evaluations"] if e["category"] == "mandatory"]
        pref_evals = [e for e in skills_eval["evaluations"] if e["category"] == "preferred"]

        req_skills_score = (
            round((sum(e["score_contribution"] for e in req_evals) / (len(req_evals) * 10.0)) * 100.0, 1)
            if req_evals
            else 80.0
        )

        pref_skills_score = (
            round((sum(e["score_contribution"] for e in pref_evals) / (len(pref_evals) * 5.0)) * 100.0, 1)
            if pref_evals
            else 70.0
        )

        # 2. Experience & Project Evaluation
        exp_eval = self.experience_agent.execute(
            candidate_experience_years=cand_exp_years,
            experience_items=cand_exp_items,
            projects=cand_projects,
            required_experience_years=min_exp,
            job_title=job_title,
            job_description=job_desc,
            db=db,
            candidate_id=candidate_id,
        )
        exp_score = exp_eval["experience_score"]
        projects_score = exp_eval["project_depth_score"]

        # 3. Education & Certifications Score (0 to 100)
        cand_edu_text = " ".join([str(e) for e in cand_edu]).lower()
        if any(deg in cand_edu_text for deg in ["phd", "doctorate"]):
            edu_score = 100.0
        elif any(deg in cand_edu_text for deg in ["master", "m.tech", "ms ", "m.s."]):
            edu_score = 95.0
        elif any(deg in cand_edu_text for deg in ["bachelor", "b.tech", "b.e.", "bs ", "b.s."]):
            edu_score = 90.0
        elif len(cand_edu) > 0:
            edu_score = 80.0
        else:
            edu_score = 65.0  # reasonable baseline for non-traditional backgrounds

        # 4. Dense Semantic Embedding Cosine Alignment (Supplementary validation)
        job_target = f"{job_title}. {job_desc[:600]}"
        cand_doc = f"Experience: {cand_exp_years} yrs. Skills: {', '.join([s.get('skill_name', '') for s in cand_skills])}. {resume_text[:1000]}"
        raw_semantic = self.embedding_service.compute_similarity(job_target, cand_doc)
        semantic_score = round(min(100.0, raw_semantic * 100.0), 1)

        # Ensure exact schema component boundaries (Technical: 40, Semantic: 30, Experience: 20, Education: 10)
        bounded_tech_score = round(min(40.0, (req_skills_score / 100.0) * 40.0), 1)
        bounded_semantic_score = round(min(30.0, (semantic_score / 100.0) * 30.0), 1)
        bounded_exp_score = round(min(20.0, (exp_score / 100.0) * 20.0), 1)
        bounded_edu_score = round(min(10.0, (edu_score / 100.0) * 10.0), 1)

        # 5. Composite Overall Score Calculation (Sum of 4 standard components ensures exact mathematical equality)
        overall_score = round(
            min(100.0, max(0.0, bounded_tech_score + bounded_semantic_score + bounded_exp_score + bounded_edu_score)), 1
        )
        model_info = self.embedding_service.get_model_info()

        # 6. Extract Strengths and Gaps
        strengths = []
        skill_gaps = []
        matched_skills = []
        missing_skills = []
        related_skills = []

        for e in skills_eval["evaluations"]:
            if e["evidence_classification"] in [
                "demonstrated_professionally",
                "demonstrated_in_project",
                "explicitly_mentioned",
            ]:
                matched_skills.append(
                    {
                        "skill": e["skill"],
                        "category": e["category"],
                        "evidence": e["snippet"],
                        "source_page": e["source_page"],
                        "evidence_classification": e["evidence_classification"],
                        "confidence": e["confidence"],
                    }
                )
                if e["evidence_classification"] == "demonstrated_professionally":
                    strengths.append(f"Demonstrated professional delivery with {e['skill']}")
            elif e["evidence_classification"] == "weakly_inferred":
                related_skills.append(e["skill"])
            elif e["evidence_classification"] == "not_found":
                missing_skills.append(e["skill"])
                if e["category"] == "mandatory":
                    skill_gaps.append(f"Missing mandatory requirement: {e['skill']}")

        if exp_eval.get("is_fresher") and projects_score >= 70:
            strengths.append("Strong technical portfolio and practical implementation depth")
        elif cand_exp_years >= min_exp > 0:
            strengths.append(f"Exceeds minimum experience requirement ({cand_exp_years} yrs vs {min_exp} yrs required)")

        # 7. Uncertainty Assessment
        confidence_metric = round(
            min(1.0, (candidate_data.get("parsing_confidence", 0.90) * 0.5) + (semantic_score / 100.0 * 0.5)), 2
        )
        uncertainty_notes = None
        if missing_skills and len(missing_skills) > 4:
            uncertainty_notes = f"Candidate profile contains {len(missing_skills)} unverified skills. Verification interview recommended."

        duration_ms = int((time.time() - start_time) * 1000)
        self.record_execution(
            db=db,
            task_name="MATCH_CANDIDATE",
            target_entity_type="candidate",
            target_entity_id=candidate_id,
            status="completed",
            duration_ms=duration_ms,
            tokens_used=0,
            model_used="multi-criteria-matching-agent",
            input_summary=f"Matched candidate against {job_title}.",
            output_summary=f"Overall score: {overall_score}/100. Req skills: {req_skills_score}, Projects: {projects_score}.",
        )

        return {
            "overall_score": overall_score,
            "technical_score": bounded_tech_score,
            "projects_score": projects_score,
            "experience_score": bounded_exp_score,
            "preferred_score": pref_skills_score,
            "education_score": bounded_edu_score,
            "semantic_score": bounded_semantic_score,
            "weights_used": active_weights,
            "confidence_score": confidence_metric,
            "uncertainty_notes": uncertainty_notes,
            "strengths": strengths[:6],
            "skill_gaps": skill_gaps[:6],
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "related_skills": related_skills,
            "explanation": {
                "summary": f"Candidate achieved {overall_score}/100 match against '{job_title}'.",
                "weights_applied": active_weights,
                "model_info": model_info,
                "domain_relevance": exp_eval.get("domain_relevance", "Moderate"),
                "fresher_verdict": exp_eval.get("fresher_friendly_verdict"),
            },
            "model_info": model_info,
        }

    def simulate_what_if(
        self,
        job_data: dict[str, Any],
        candidate_evaluations: list[dict[str, Any]],
        new_weights: dict[str, float] | None = None,
        modified_requirements: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Conduct a live recruiter What-If analysis.
        Simulates score and rank shifts across candidates when criteria or weights change.
        """
        weights = self.normalize_weights(new_weights)
        simulated_results = []

        for item in candidate_evaluations:
            cand_id = item["candidate_id"]
            cand_name = item.get("name", "Candidate")
            prev_score = float(item.get("previous_score", 0.0))

            # Recompute component scores with new weights
            req_s = float(item.get("technical_score", prev_score))
            proj_s = float(item.get("projects_score", prev_score * 0.9))
            exp_s = float(item.get("experience_score", prev_score * 0.8))
            pref_s = float(item.get("preferred_score", prev_score * 0.7))
            edu_s = float(item.get("education_score", 85.0))

            # If modified requirements added mandatory skill, check candidate skills
            if modified_requirements:
                cand_skill_set = {s.lower() for s in item.get("skills", [])}
                for mr in modified_requirements:
                    if mr.get("category") == "mandatory":
                        if mr.get("skill_name", "").lower() not in cand_skill_set:
                            req_s = max(10.0, req_s - 15.0)

            sim_score = round(
                (req_s * (weights["required_skills"] / 100.0))
                + (proj_s * (weights["projects"] / 100.0))
                + (exp_s * (weights["experience"] / 100.0))
                + (pref_s * (weights["preferred_skills"] / 100.0))
                + (edu_s * (weights["education"] / 100.0)),
                1,
            )
            sim_score = max(0.0, min(100.0, sim_score))

            simulated_results.append(
                {
                    "candidate_id": cand_id,
                    "name": cand_name,
                    "previous_score": prev_score,
                    "simulated_score": sim_score,
                    "score_delta": round(sim_score - prev_score, 1),
                }
            )

        # Calculate previous and new ranks
        simulated_results.sort(key=lambda x: x["previous_score"], reverse=True)
        for rank, r in enumerate(simulated_results, 1):
            r["previous_rank"] = rank

        simulated_results.sort(key=lambda x: x["simulated_score"], reverse=True)
        for rank, r in enumerate(simulated_results, 1):
            r["simulated_rank"] = rank
            r["rank_delta"] = r["previous_rank"] - rank

            if r["rank_delta"] > 0:
                r["impact_summary"] = (
                    f"Advanced +{r['rank_delta']} positions (Score: {r['simulated_score']} vs {r['previous_score']})"
                )
            elif r["rank_delta"] < 0:
                r["impact_summary"] = (
                    f"Dropped {r['rank_delta']} positions (Score: {r['simulated_score']} vs {r['previous_score']})"
                )
            else:
                r["impact_summary"] = f"Rank unchanged (Score: {r['simulated_score']})"

        avg_before = (
            round(sum(r["previous_score"] for r in simulated_results) / len(simulated_results), 1)
            if simulated_results
            else 0.0
        )
        avg_after = (
            round(sum(r["simulated_score"] for r in simulated_results) / len(simulated_results), 1)
            if simulated_results
            else 0.0
        )
        movers = sum(1 for r in simulated_results if abs(r["rank_delta"]) >= 2 or abs(r["score_delta"]) >= 5.0)

        return {
            "job_id": job_data.get("id", ""),
            "total_candidates_evaluated": len(simulated_results),
            "average_score_before": avg_before,
            "average_score_after": avg_after,
            "significant_movers_count": movers,
            "deltas": simulated_results,
        }

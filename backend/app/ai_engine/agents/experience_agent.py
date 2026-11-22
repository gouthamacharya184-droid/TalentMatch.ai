import logging
import re
import time
from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ExperienceEvaluationAgent(BaseAgent):
    """
    Agent 4: Experience Evaluation Agent.
    Evaluates candidate professional history, internships, and project depth.
    Enforces fair, non-discriminatory evaluation for freshers and early-career talent,
    valuing demonstrated accomplishments and hands-on delivery over raw calendar tenure.
    """

    def __init__(self):
        super().__init__(
            agent_name="ExperienceEvaluationAgent",
            description="Evaluates professional accomplishments, project implementation depth, and domain relevance without penalizing freshers.",
        )

    def execute(
        self,
        candidate_experience_years: float,
        experience_items: list[dict[str, Any]],
        projects: list[dict[str, Any]],
        required_experience_years: float,
        job_title: str,
        job_description: str,
        db: Session | None = None,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        """Assess career trajectory, project complexity, and domain relevance."""
        start_time = time.time()

        is_fresher = candidate_experience_years <= 1.0 and len(experience_items) <= 1
        has_internships = any("intern" in (e.get("role", "") + e.get("title", "")).lower() for e in experience_items)
        has_substantial_projects = len(projects) >= 2 or any(len(p.get("description", "")) > 100 for p in projects)

        # 1. Experience score calculation (0 to 100)
        # Avoid zero score even if years < required if strong projects exist
        if required_experience_years <= 0.0:
            tenure_score = 90.0
        elif candidate_experience_years >= required_experience_years:
            # Full base for meeting requirement + slight scaling
            ratio = candidate_experience_years / required_experience_years
            tenure_score = min(100.0, 85.0 + min(15.0, (ratio - 1.0) * 10.0))
        else:
            # Proportional score, with floor protected by projects/internships
            raw_ratio = candidate_experience_years / required_experience_years
            if is_fresher and (has_substantial_projects or has_internships):
                # Fair fresher adjustment: reward demonstrated project execution
                tenure_score = max(55.0, raw_ratio * 70.0 + 35.0)
            else:
                tenure_score = max(30.0, raw_ratio * 80.0)

        # 2. Project Depth Score (0 to 100)
        project_points = 50.0  # baseline
        if len(projects) >= 1:
            project_points += 15.0
        if len(projects) >= 3:
            project_points += 15.0

        # Check for technical depth keywords in projects
        combined_projects = " ".join(p.get("description", "") + " " + p.get("title", "") for p in projects).lower()
        impact_keywords = [
            "deployed",
            "production",
            "optimized",
            "architected",
            "api",
            "database",
            "scaled",
            "docker",
            "pipeline",
            "ml",
            "ai",
        ]
        hits = sum(1 for kw in impact_keywords if kw in combined_projects)
        project_points += min(20.0, hits * 3.5)
        project_depth_score = min(100.0, round(project_points, 1))

        # 3. Domain relevance
        job_keywords = set(re.findall(r"\b[a-z]{4,}\b", job_title.lower() + " " + job_description[:500].lower()))
        cand_history_words = set(
            re.findall(
                r"\b[a-z]{4,}\b",
                combined_projects + " " + " ".join(e.get("role", "") for e in experience_items).lower(),
            )
        )
        common_domain_terms = job_keywords.intersection(cand_history_words)

        if len(common_domain_terms) > 8:
            domain_relevance = "High"
        elif len(common_domain_terms) > 3:
            domain_relevance = "Moderate"
        else:
            domain_relevance = "Transferable"

        # 4. Trajectory analysis
        if is_fresher:
            seniority_level = "Entry / Fresher"
            trajectory = (
                "Early-career talent demonstrating practical delivery through personal/academic portfolios. "
                "Strong candidate for development and mentorship without rigid tenure bias."
            )
        elif candidate_experience_years < 3.0:
            seniority_level = "Junior / Associate"
            trajectory = "Demonstrating consistent hands-on execution and technical foundational progression."
        elif candidate_experience_years < 6.0:
            seniority_level = "Mid-Level Professional"
            trajectory = "Solid multi-year implementation experience delivering production solutions."
        else:
            seniority_level = "Senior / Lead"
            trajectory = "Extensive industry tenure with demonstrated systems ownership and technical leadership."

        # Extract accomplishments
        accomplishments = []
        for p in projects[:3]:
            if p.get("title"):
                accomplishments.append(f"Engineered '{p['title']}': {p.get('description', '')[:100]}")
        for e in experience_items[:2]:
            if e.get("role") and e.get("company"):
                accomplishments.append(f"Served as {e['role']} at {e['company']}")

        final_exp_score = round((tenure_score * 0.6) + (project_depth_score * 0.4), 1)
        duration_ms = int((time.time() - start_time) * 1000)

        self.record_execution(
            db=db,
            task_name="EVALUATE_EXPERIENCE",
            target_entity_type="candidate",
            target_entity_id=candidate_id,
            status="completed",
            duration_ms=duration_ms,
            tokens_used=0,
            model_used="career-trajectory-evaluator",
            input_summary=f"Evaluated {candidate_experience_years} yrs against {required_experience_years} yrs required.",
            output_summary=f"Experience score: {final_exp_score}/100. Level: {seniority_level}.",
        )

        return {
            "experience_score": final_exp_score,
            "project_depth_score": project_depth_score,
            "seniority_level": seniority_level,
            "domain_relevance": domain_relevance,
            "trajectory_analysis": trajectory,
            "is_fresher": is_fresher,
            "fresher_friendly_verdict": (
                "Demonstrated project depth compensates for lack of formal enterprise tenure."
                if (is_fresher and project_depth_score >= 65.0)
                else "Standard tenure evaluation applied."
            ),
            "key_accomplishments": accomplishments,
        }

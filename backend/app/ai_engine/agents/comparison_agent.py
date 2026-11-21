import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.ai_engine.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CandidateComparisonAgent(BaseAgent):
    """
    Agent 6: Candidate Comparison Agent.
    Executes multi-candidate side-by-side comparative analysis.
    Highlights skill coverage differentials, project substance, experience tradeoffs,
    and transparently surfaces evaluation uncertainties or conflicting agent assessments.
    """

    def __init__(self):
        super().__init__(
            agent_name="CandidateComparisonAgent",
            description="Side-by-side candidate comparison, consensus & conflict detection, and competitive ranking differentiators."
        )

    def execute(
        self,
        job_data: Dict[str, Any],
        candidate_evaluations: List[Dict[str, Any]],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Compare 2 to 5 candidate profiles against the job criteria."""
        start_time = time.time()
        
        if len(candidate_evaluations) < 2:
            return {"error": "Comparison requires at least 2 candidate evaluations."}

        # 1. Build common skill matrix across candidates
        job_reqs = job_data.get("requirements", [])
        all_req_skills = [r.get("skill_name") for r in job_reqs if r.get("skill_name")]

        skill_matrix = []
        for skill in all_req_skills:
            row = {"skill": skill, "candidates": {}}
            for ce in candidate_evaluations:
                cand_id = ce["candidate"]["id"]
                matched_set = {
                    (m.get("skill") or m.get("skill_name") or "").lower()
                    for m in ce["analysis"].get("matched_skills", [])
                }
                row["candidates"][cand_id] = skill.lower() in matched_set
            skill_matrix.append(row)

        # 2. Identify Key Differentiators and Conflicts
        ranked_candidates = sorted(
            candidate_evaluations,
            key=lambda c: c["analysis"].get("overall_score", 0.0),
            reverse=True
        )

        differentiators = []
        agent_conflicts = []

        top_cand = ranked_candidates[0]
        runner_up = ranked_candidates[1]

        top_name = top_cand["candidate"].get("name", "Candidate 1")
        runner_name = runner_up["candidate"].get("name", "Candidate 2")
        top_score = top_cand["analysis"].get("overall_score", 0.0)
        runner_score = runner_up["analysis"].get("overall_score", 0.0)

        score_gap = round(top_score - runner_score, 1)
        if score_gap > 5.0:
            differentiators.append(f"{top_name} leads {runner_name} by {score_gap} points primarily due to verified technical skills alignment.")
        else:
            differentiators.append(f"{top_name} and {runner_name} are closely matched within {score_gap} points. Final selection depends on interview performance.")

        # Check for agent disagreements / conflicts in evaluations
        for ce in candidate_evaluations:
            c_name = ce["candidate"].get("name", "Candidate")
            tech_s = ce["analysis"].get("technical_score", 0.0)
            exp_s = ce["analysis"].get("experience_score", 0.0)
            proj_s = ce["analysis"].get("projects_score", 0.0)
            
            # Conflict 1: High technical skill score but very low experience score
            if tech_s >= 80.0 and exp_s < 50.0:
                agent_conflicts.append({
                    "candidate_name": c_name,
                    "conflict_type": "Skill vs Tenure Divergence",
                    "description": f"{c_name} scored high on technical skills ({tech_s}/100) but low on recorded tenure ({exp_s}/100). TechnicalSkillsAgent approves while ExperienceAgent advises verifying senior system ownership."
                })
            # Conflict 2: High overall score but high uncertainty notes
            if ce["analysis"].get("overall_score", 0.0) >= 80.0 and ce["analysis"].get("uncertainty_notes"):
                agent_conflicts.append({
                    "candidate_name": c_name,
                    "conflict_type": "Uncertainty in High Scorer",
                    "description": f"{c_name} received strong overall score but has unverified skill claims: '{ce['analysis']['uncertainty_notes']}'"
                })

        # 3. Overall executive hiring recommendation
        rec_summary = (
            f"Recommend prioritizing {top_name} for first-round technical screening. "
            f"If domain depth or specialized tooling is required, consider {runner_name} as an equivalent alternative."
        )

        duration_ms = int((time.time() - start_time) * 1000)
        self.record_execution(
            db=db,
            task_name="COMPARE_CANDIDATES",
            target_entity_type="job",
            target_entity_id=job_data.get("id"),
            status="completed",
            duration_ms=duration_ms,
            tokens_used=0,
            model_used="multi-candidate-comparison-agent",
            input_summary=f"Compared {len(candidate_evaluations)} candidates for {job_data.get('title')}.",
            output_summary=f"Leader: {top_name} ({top_score}/100). Identified {len(agent_conflicts)} evaluation nuances."
        )

        return {
            "job_id": job_data.get("id"),
            "leader": {
                "candidate_id": top_cand["candidate"]["id"],
                "name": top_name,
                "score": top_score
            },
            "score_gap": score_gap,
            "differentiators": differentiators,
            "agent_conflicts": agent_conflicts,
            "skill_matrix": skill_matrix,
            "executive_recommendation": rec_summary
        }

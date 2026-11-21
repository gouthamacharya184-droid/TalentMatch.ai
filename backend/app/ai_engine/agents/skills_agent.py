import time
import json
import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.ai_engine.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TechnicalSkillsAgent(BaseAgent):
    """
    Agent 3: Technical Skills Evaluation Agent.
    Evaluates candidate technical competencies against required and preferred job criteria.
    Classifies every skill's evidence level:
      - explicitly_mentioned
      - demonstrated_in_project
      - demonstrated_professionally
      - weakly_inferred
      - not_found
      - unable_to_verify
    Provides supporting text snippets, page numbers, and confidence metrics for complete auditability.
    """

    def __init__(self):
        super().__init__(
            agent_name="TechnicalSkillsEvaluationAgent",
            description="Assesses programming languages, frameworks, and tools with 6-tier evidence classification and source page citations."
        )

    def execute(
        self,
        job_requirements: List[Dict[str, Any]],
        candidate_skills: List[Dict[str, Any]],
        candidate_projects: List[Dict[str, Any]],
        candidate_experience: List[Dict[str, Any]],
        resume_text: str,
        page_texts: Optional[Dict[str, str]] = None,
        db: Optional[Session] = None,
        candidate_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute granular technical skills evaluation with evidence citations."""
        start_time = time.time()
        
        cand_skill_map = {s.get("skill_name", "").lower(): s for s in candidate_skills}
        cand_skill_names = set(cand_skill_map.keys())
        full_text_lower = resume_text.lower()
        pages = page_texts if page_texts else {"1": resume_text}

        evaluations: List[Dict[str, Any]] = []
        earned_points = 0.0
        total_possible_points = 0.0

        for req in job_requirements:
            req_skill = req.get("skill_name", "")
            req_lower = req_skill.lower()
            category = req.get("category", "mandatory")
            weight = float(req.get("weight", 1.0 if category == "mandatory" else 0.5))
            total_possible_points += weight * 10.0

            evidence_class = "not_found"
            source_page = 1
            snippet = f"Skill '{req_skill}' was not identified in the submitted resume document."
            confidence = 0.0
            score_contribution = 0.0

            # 1. Check if directly in candidate skill map
            if req_lower in cand_skill_names:
                skill_obj = cand_skill_map[req_lower]
                source_page = skill_obj.get("source_page", 1)
                snippet = skill_obj.get("snippet", f"Explicitly listed under candidate skills.")

                # Check if demonstrated professionally or in project
                prof_match = self._find_in_collection(req_lower, candidate_experience)
                proj_match = self._find_in_collection(req_lower, candidate_projects)

                if prof_match:
                    evidence_class = "demonstrated_professionally"
                    snippet = f"Used professionally in role '{prof_match.get('role', 'Engineer')}' at {prof_match.get('company', 'Company')}."
                    source_page = prof_match.get("source_page", source_page)
                    confidence = 0.98
                    score_contribution = weight * 10.0
                elif proj_match:
                    evidence_class = "demonstrated_in_project"
                    snippet = f"Implemented in project '{proj_match.get('title', 'Project')}': {proj_match.get('description', '')[:120]}."
                    source_page = proj_match.get("source_page", source_page)
                    confidence = 0.92
                    score_contribution = weight * 8.5
                else:
                    evidence_class = "explicitly_mentioned"
                    confidence = 0.85
                    score_contribution = weight * 7.0

            # 2. Check if mentioned anywhere in raw text or pages
            elif req_lower in full_text_lower:
                source_page, snippet = self._find_text_snippet(req_lower, pages)
                proj_match = self._find_in_collection(req_lower, candidate_projects)
                if proj_match:
                    evidence_class = "demonstrated_in_project"
                    confidence = 0.88
                    score_contribution = weight * 8.0
                else:
                    evidence_class = "explicitly_mentioned"
                    confidence = 0.80
                    score_contribution = weight * 6.5

            # 3. Check for related or weakly inferred competency
            else:
                inferred = self._check_inferred_competency(req_lower, cand_skill_names)
                if inferred:
                    evidence_class = "weakly_inferred"
                    snippet = f"Inferred through candidate proficiency in related technology '{inferred}'."
                    confidence = 0.65
                    score_contribution = weight * 5.0
                else:
                    evidence_class = "not_found"
                    confidence = 1.0
                    score_contribution = 0.0

            earned_points += score_contribution
            evaluations.append({
                "skill": req_skill,
                "category": category,
                "evidence_classification": evidence_class,
                "source_page": source_page,
                "snippet": snippet,
                "confidence": confidence,
                "weight": weight,
                "score_contribution": round(score_contribution, 2)
            })

        # Calculate normalized score (0 to 100)
        norm_score = round((earned_points / total_possible_points) * 100.0, 1) if total_possible_points > 0 else 75.0
        duration_ms = int((time.time() - start_time) * 1000)

        self.record_execution(
            db=db,
            task_name="EVALUATE_TECHNICAL_SKILLS",
            target_entity_type="candidate",
            target_entity_id=candidate_id,
            status="completed",
            duration_ms=duration_ms,
            tokens_used=0,
            model_used="evidence-classification-engine",
            input_summary=f"Evaluated {len(job_requirements)} requirements against candidate profile.",
            output_summary=f"Technical score: {norm_score}/100. Verified {sum(1 for e in evaluations if e['evidence_classification'] != 'not_found')} skills."
        )

        return {
            "technical_score": norm_score,
            "evaluations": evaluations,
            "matched_count": sum(1 for e in evaluations if e["evidence_classification"] in ["demonstrated_professionally", "demonstrated_in_project", "explicitly_mentioned"]),
            "missing_count": sum(1 for e in evaluations if e["evidence_classification"] == "not_found"),
            "inferred_count": sum(1 for e in evaluations if e["evidence_classification"] == "weakly_inferred")
        }

    def _find_in_collection(self, skill_lower: str, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for item in items:
            combined = json.dumps(item).lower()
            if skill_lower in combined:
                return item
        return None

    def _find_text_snippet(self, term: str, pages: Dict[str, str]) -> (int, str):
        for p_num, text in pages.items():
            idx = text.lower().find(term)
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(text), idx + len(term) + 60)
                snippet = text[start:end].replace("\n", " ").strip()
                page_int = int(p_num) if p_num.isdigit() else 1
                return page_int, snippet
        return 1, f"Term '{term}' located in resume document."

    def _check_inferred_competency(self, target_skill: str, candidate_skills: set) -> Optional[str]:
        # Semantic/family relationships
        families = {
            "fastapi": ["python", "flask", "django", "pydantic", "starlette"],
            "react": ["javascript", "typescript", "vue", "frontend", "html", "css", "redux"],
            "docker": ["kubernetes", "containerization", "devops", "ci/cd"],
            "postgresql": ["sql", "mysql", "databases", "relational database", "sqlite"],
            "aws": ["cloud", "gcp", "azure", "ec2", "s3"],
            "pytorch": ["deep learning", "machine learning", "tensorflow", "keras", "python"],
            "sentence-transformers": ["nlp", "embeddings", "transformers", "pytorch", "huggingface"]
        }
        for parent, relations in families.items():
            if target_skill == parent:
                for r in relations:
                    if r in candidate_skills:
                        return r
            elif target_skill in relations:
                if parent in candidate_skills:
                    return parent
        return None

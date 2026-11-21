import time
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.ai_engine.agents.base_agent import BaseAgent
from app.ai_engine.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)


class JobDescriptionAgent(BaseAgent):
    """
    Agent 1: Job Description Intelligence Agent.
    Analyzes raw job descriptions, extracts structured requirements, identifies
    seniority and skill hierarchies, detects requirement conflicts or ambiguities,
    and stages criteria for recruiter review and approval.
    """

    def __init__(self):
        super().__init__(
            agent_name="JobDescriptionIntelligenceAgent",
            description="Extracts and normalizes role requirements, seniority, mandatory vs preferred skills, and detects criteria conflicts."
        )
        self.skill_extractor = SkillExtractor()

    def execute(
        self,
        job_text: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        db: Optional[Session] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute JD intelligence extraction with LLM reasoning and rule-based fallback."""
        start_time = time.time()
        tokens_est = len(job_text.split()) * 2

        # 1. Check if LLM is active
        if self.llm_service.is_available():
            try:
                llm_result = self._extract_via_llm(job_text, job_title, company)
                if llm_result and isinstance(llm_result, dict) and "mandatory_skills" in llm_result:
                    duration_ms = int((time.time() - start_time) * 1000)
                    self.record_execution(
                        db=db,
                        task_name="ANALYZE_JOB_DESCRIPTION",
                        target_entity_type="job",
                        target_entity_id=job_id,
                        status="completed",
                        duration_ms=duration_ms,
                        tokens_used=tokens_est + 500,
                        input_summary=f"Analyzed JD: {job_title or 'Untitled'} ({len(job_text)} chars)",
                        output_summary=f"Extracted {len(llm_result.get('mandatory_skills', []))} mandatory, {len(llm_result.get('preferred_skills', []))} preferred skills."
                    )
                    return llm_result
            except Exception as e:
                logger.warning(f"JobDescriptionAgent LLM execution failed: {e}. Running deterministic fallback.")

        # 2. Deterministic Heuristic Fallback Engine
        fallback_result = self._extract_deterministic(job_text, job_title, company)
        duration_ms = int((time.time() - start_time) * 1000)
        self.record_execution(
            db=db,
            task_name="ANALYZE_JOB_DESCRIPTION",
            target_entity_type="job",
            target_entity_id=job_id,
            status="fallback",
            duration_ms=duration_ms,
            tokens_used=0,
            model_used="deterministic-rule-engine",
            input_summary=f"Analyzed JD: {job_title or 'Untitled'} ({len(job_text)} chars)",
            output_summary=f"Fallback extracted {len(fallback_result.get('mandatory_skills', []))} mandatory skills."
        )
        return fallback_result

    def _extract_via_llm(self, job_text: str, job_title: Optional[str], company: Optional[str]) -> Optional[Dict[str, Any]]:
        framed_jd = self.frame_data("job_description", job_text)
        prompt = f"""
You are the Job Description Intelligence Agent for an enterprise recruitment platform.
Analyze the following job description document and extract complete, structured criteria.

{framed_jd}

Requirements for extraction:
1. Identify the exact job title and seniority level (Junior, Mid-Level, Senior, Lead, Staff, Principal, Director).
2. Distinguish strictly between 'mandatory' (must-have) and 'preferred' (nice-to-have) skills.
3. Classify skill types: 'programming_language', 'framework', 'database', 'cloud_devops', 'tool', or 'methodology'.
4. Extract minimum experience required in years as a float (e.g. 3.0, 5.0, 0.0 for freshers).
5. Extract formal education requirements (e.g. Bachelor's in CS, Master's, Any Engineering, High School).
6. Extract key responsibilities as a concise list of strings.
7. Detect ambiguities or conflicting criteria (e.g. "Senior Architect requiring 1 year experience", or conflicting technology versions).
8. Recommend realistic scoring weights based on role seniority (sum of weights must be 100%).

Return valid JSON with this exact schema:
{{
  "title": "<Extracted Job Title>",
  "seniority": "<Junior | Mid-Level | Senior | Lead | Staff | Principal>",
  "min_experience": 0.0,
  "education_req": "<Education Requirement>",
  "mandatory_skills": [
    {{"skill_name": "<Skill>", "category": "mandatory", "skill_type": "<type>", "weight": 1.0}}
  ],
  "preferred_skills": [
    {{"skill_name": "<Skill>", "category": "preferred", "skill_type": "<type>", "weight": 0.5}}
  ],
  "responsibilities": ["<Responsibility 1>", "<Responsibility 2>"],
  "ambiguities_or_conflicts": ["<Any detected conflicts or 'None detected'>"],
  "recommended_weights": {{
    "required_skills": 35.0,
    "projects": 25.0,
    "experience": 15.0,
    "preferred_skills": 15.0,
    "education": 10.0
  }},
  "extraction_confidence": 0.95
}}
"""
        return self.llm_service.generate_json(prompt)

    def _extract_deterministic(self, job_text: str, job_title: Optional[str], company: Optional[str]) -> Dict[str, Any]:
        """High-precision regex and dictionary NLP extraction."""
        import re
        extracted_skills = self.skill_extractor.extract_skills(job_text)
        
        # Seniority detection
        lower_text = (job_title or "" + " " + job_text).lower()
        seniority = "Mid-Level"
        if any(w in lower_text for w in ["principal", "director", "architect"]):
            seniority = "Principal"
        elif any(w in lower_text for w in ["staff", "head of", "vp"]):
            seniority = "Staff"
        elif any(w in lower_text for w in ["lead", "tech lead"]):
            seniority = "Lead"
        elif any(w in lower_text for w in ["senior", "sr.", "sr "]):
            seniority = "Senior"
        elif any(w in lower_text for w in ["junior", "jr.", "entry", "intern", "associate", "fresher"]):
            seniority = "Junior"

        # Experience extraction
        min_exp = 0.0
        exp_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:to\s*\d+)?\s*(?:years?|yrs?)\b", lower_text)
        if exp_match:
            try:
                min_exp = float(exp_match.group(1))
            except Exception:
                pass

        # Split mandatory vs preferred
        mandatory: List[Dict[str, Any]] = []
        preferred: List[Dict[str, Any]] = []

        for idx, item in enumerate(extracted_skills):
            skill_dict = {
                "skill_name": item["skill_name"],
                "skill_type": item["category"],
                "category": "mandatory" if idx < 5 else "preferred",
                "weight": 1.0 if idx < 5 else 0.5
            }
            if idx < 5:
                mandatory.append(skill_dict)
            else:
                preferred.append(skill_dict)

        # Education
        edu_req = "Bachelor's Degree in Computer Science or related field"
        if "master" in lower_text or "m.tech" in lower_text:
            edu_req = "Master's Degree in Computer Science or related field"
        elif "phd" in lower_text or "doctorate" in lower_text:
            edu_req = "PhD in relevant technical discipline"

        # Ambiguity check
        ambiguities = []
        if seniority in ["Senior", "Lead", "Principal"] and min_exp < 2.0 and min_exp > 0:
            ambiguities.append(f"Seniority '{seniority}' conflicts with low experience threshold ({min_exp} yrs).")
        if not mandatory:
            ambiguities.append("No explicit core technical skills detected in job text.")

        # Title extraction from text if not provided
        extracted_title = job_title
        if not extracted_title:
            title_match = re.search(r"(?:Job Title|Role|Position|Title)\s*:\s*([^|\n\r]+)", job_text, re.IGNORECASE)
            if title_match:
                extracted_title = title_match.group(1).strip()
            else:
                for line in [l.strip() for l in job_text.splitlines() if l.strip()][:5]:
                    if len(line) < 60 and any(w in line.lower() for w in ["engineer", "developer", "architect", "lead", "manager"]):
                        extracted_title = line
                        break
        if not extracted_title:
            extracted_title = "Software Engineer"

        return {
            "title": extracted_title,
            "seniority": seniority,
            "min_experience": min_exp,
            "education_req": edu_req,
            "mandatory_skills": mandatory,
            "preferred_skills": preferred,
            "responsibilities": [
                "Design, build, and deploy reliable software systems and services.",
                "Collaborate with cross-functional product and engineering teams.",
                "Participate in code reviews, architectural discussions, and technical mentorship."
            ],
            "ambiguities_or_conflicts": ambiguities if ambiguities else ["None detected"],
            "recommended_weights": {
                "required_skills": 35.0,
                "projects": 25.0,
                "experience": 15.0,
                "preferred_skills": 15.0,
                "education": 10.0
            },
            "extraction_confidence": 0.85
        }

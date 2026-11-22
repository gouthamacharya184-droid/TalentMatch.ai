import time
import hashlib
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.ai_engine.agents.base_agent import BaseAgent
from app.ai_engine.skill_extractor import SkillExtractor
from app.parsers.resume_parser import ResumeParser

logger = logging.getLogger(__name__)


class ResumeIntelligenceAgent(BaseAgent):
    """
    Agent 2: Resume Intelligence Agent.
    Ingests and normalizes resume documents across PDF, DOCX, and TXT formats.
    Extracts deep candidate profiles, maps every fact to exact source document pages,
    detects parsing anomalies, and assesses profile completeness.
    """

    def __init__(self):
        super().__init__(
            agent_name="ResumeIntelligenceAgent",
            description="Deep multi-page document parsing, structural extraction, page-level citation mapping, and profile completeness validation."
        )
        self.base_parser = ResumeParser()
        self.skill_extractor = SkillExtractor()

    def compute_hash(self, content_bytes: bytes) -> str:
        """Compute SHA-256 hash of raw document for duplicate detection."""
        return hashlib.sha256(content_bytes).hexdigest()

    def execute(
        self,
        raw_text: str,
        page_texts: Optional[Dict[str, str]] = None,
        filename: Optional[str] = None,
        file_size: int = 0,
        content_hash: Optional[str] = None,
        db: Optional[Session] = None,
        candidate_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute resume intelligence parsing and citation tracking."""
        start_time = time.time()
        tokens_est = len(raw_text.split()) * 2

        if not raw_text.strip():
            return self._empty_response(filename, content_hash)

        # 1. Base parsing with per-page text segmentation
        profile = self.base_parser.parse(raw_text, filename=filename)

        # 2. Enrich with page mapping for every extracted skill and project
        enriched_skills = self._map_skills_to_pages(profile.get("skills", []), page_texts, raw_text)
        enriched_projects = self._extract_projects_with_pages(profile.get("projects", []), page_texts, raw_text)
        enriched_experience = self._map_experience_to_pages(profile.get("experience", []), page_texts)

        # 3. Completeness and confidence evaluation
        completeness_status, confidence_score = self._evaluate_completeness(profile)

        result = {
            "name": profile.get("name") or "Candidate",
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "location": profile.get("location") or "Remote / Flexible",
            "total_experience_years": profile.get("total_experience_years", 0.0),
            "education": profile.get("education", []),
            "experience": enriched_experience,
            "projects": enriched_projects,
            "certifications": profile.get("certifications", []),
            "skills": enriched_skills,
            "page_count": len(page_texts) if page_texts else 1,
            "content_hash": content_hash,
            "parsing_confidence": confidence_score,
            "completeness_status": completeness_status,
            "raw_text": raw_text,
            "page_texts": page_texts or {"1": raw_text}
        }

        duration_ms = int((time.time() - start_time) * 1000)
        self.record_execution(
            db=db,
            task_name="PARSE_RESUME_PROFILE",
            target_entity_type="candidate",
            target_entity_id=candidate_id,
            status="completed",
            duration_ms=duration_ms,
            tokens_used=tokens_est,
            model_used="hybrid-regex-nlp-parser",
            input_summary=f"Parsed {filename or 'Resume'} ({len(raw_text)} chars, {len(page_texts or {})} pages)",
            output_summary=f"Extracted {len(enriched_skills)} skills, {len(enriched_projects)} projects, {profile.get('total_experience_years', 0)} years exp."
        )

        return result

    def _map_skills_to_pages(
        self,
        extracted_skills: List[Dict[str, Any]],
        page_texts: Optional[Dict[str, str]],
        raw_text: str
    ) -> List[Dict[str, Any]]:
        """Map each extracted skill to its primary source page and snippet citation."""
        enriched = []
        pages = page_texts if page_texts else {"1": raw_text}

        for s in extracted_skills:
            skill_name = s.get("skill_name", "")
            s_lower = skill_name.lower()
            
            found_page = 1
            snippet = f"Skill '{skill_name}' identified in resume competencies."
            evidence_type = "explicit"

            for page_num_str, p_text in pages.items():
                p_lower = p_text.lower()
                idx = p_lower.find(s_lower)
                if idx != -1:
                    found_page = int(page_num_str) if page_num_str.isdigit() else 1
                    # Extract surrounding snippet (120 chars around match)
                    start_idx = max(0, idx - 40)
                    end_idx = min(len(p_text), idx + len(skill_name) + 60)
                    snippet = p_text[start_idx:end_idx].replace("\n", " ").strip()
                    
                    # Check context: project or professional
                    surrounding = p_lower[max(0, idx - 100):min(len(p_lower), idx + 100)]
                    if any(w in surrounding for w in ["project", "github", "developed", "built", "implemented"]):
                        evidence_type = "project"
                    elif any(w in surrounding for w in ["senior", "engineer", "lead", "developer", "worked at", "company", "client"]):
                        evidence_type = "professional"
                    break

            enriched.append({
                "skill_name": skill_name,
                "category": s.get("category", "technical"),
                "proficiency_level": s.get("proficiency_level", "intermediate"),
                "source_page": found_page,
                "snippet": snippet,
                "evidence_type": evidence_type
            })

        return enriched

    def _extract_projects_with_pages(
        self,
        projects: List[Dict[str, Any]],
        page_texts: Optional[Dict[str, str]],
        raw_text: str
    ) -> List[Dict[str, Any]]:
        """Ensure projects contain source page references."""
        pages = page_texts if page_texts else {"1": raw_text}
        results = []

        for p in projects:
            title = p.get("title", "Technical Project")
            found_page = 1
            for page_num_str, p_text in pages.items():
                if title.lower() in p_text.lower():
                    found_page = int(page_num_str) if page_num_str.isdigit() else 1
                    break
            
            p["source_page"] = found_page
            results.append(p)

        # If parser didn't find projects, detect common academic/personal project blocks
        if not results:
            lines = raw_text.splitlines()
            in_proj_section = False
            curr_proj = None
            
            for line in lines:
                l_lower = line.strip().lower()
                if any(h in l_lower for h in ["projects", "personal projects", "academic projects", "key projects"]):
                    in_proj_section = True
                    continue
                if in_proj_section and any(h in l_lower for h in ["experience", "education", "skills", "certifications", "interests"]):
                    in_proj_section = False
                    if curr_proj:
                        results.append(curr_proj)
                    break
                if in_proj_section and line.strip() and len(line.strip()) < 80 and not line.strip().startswith("-"):
                    if curr_proj:
                        results.append(curr_proj)
                    curr_proj = {
                        "title": line.strip(),
                        "description": "",
                        "technologies": [],
                        "source_page": 1
                    }
                elif in_proj_section and curr_proj and line.strip():
                    curr_proj["description"] += " " + line.strip()

            if curr_proj and curr_proj not in results:
                results.append(curr_proj)

        return results[:5]

    def _map_experience_to_pages(
        self,
        experience: List[Dict[str, Any]],
        page_texts: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        if not page_texts:
            return experience

        for exp in experience:
            company = exp.get("company", "").lower()
            role = exp.get("role", "").lower()
            for page_num_str, text in page_texts.items():
                t_lower = text.lower()
                if (company and company in t_lower) or (role and role in t_lower):
                    exp["source_page"] = int(page_num_str) if page_num_str.isdigit() else 1
                    break
        return experience

    def _evaluate_completeness(self, profile: Dict[str, Any]) -> (str, float):
        score = 0.0
        if profile.get("name") and profile.get("name") != "Candidate":
            score += 0.20
        if profile.get("email"):
            score += 0.20
        if profile.get("phone"):
            score += 0.15
        if profile.get("skills"):
            score += 0.20
        if profile.get("experience") or profile.get("total_experience_years", 0) > 0:
            score += 0.15
        if profile.get("education"):
            score += 0.10

        conf = round(min(1.0, score), 2)
        if conf >= 0.80:
            status = "complete"
        elif not profile.get("email") and not profile.get("phone"):
            status = "missing_contact"
        elif not profile.get("experience"):
            status = "incomplete_history"
        else:
            status = "sparse"

        return status, conf

    def _empty_response(self, filename: Optional[str], content_hash: Optional[str]) -> Dict[str, Any]:
        return {
            "name": "Candidate",
            "email": None,
            "phone": None,
            "location": "Remote / Flexible",
            "total_experience_years": 0.0,
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "skills": [],
            "page_count": 1,
            "content_hash": content_hash,
            "parsing_confidence": 0.0,
            "completeness_status": "unreadable_empty",
            "raw_text": "",
            "page_texts": {"1": ""}
        }

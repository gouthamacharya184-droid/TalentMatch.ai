from typing import List, Dict, Any
from app.ai_engine.embeddings import EmbeddingService
from app.ai_engine.skill_extractor import SkillExtractor


class MatchingEngine:
    """
    Core AI Resume Matching Engine.
    Executes a 4-component weighted matching algorithm (0 - 100 pts):
      1. Technical Skill Match: 40%
      2. Semantic Similarity: 30%
      3. Relevant Experience: 20%
      4. Education & Qualifications: 10%
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.skill_extractor = SkillExtractor()

    def match(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        candidate_skills: List[str],
        resume_text: str = ""
    ) -> Dict[str, Any]:
        """
        Compare job requirements against candidate resume and calculate
        transparent, explainable matching scores.
        """
        job_title = job_data.get("title", "")
        job_description = job_data.get("description", "")
        job_reqs = job_data.get("requirements", [])
        min_experience = float(job_data.get("min_experience", 0.0))
        education_req = str(job_data.get("education_req", "Bachelor's Degree")).lower()

        # Extract skills from job description if not explicitly provided
        if not job_reqs:
            extracted_job_skills = self.skill_extractor.extract_skills(job_description)
            job_reqs = [
                {
                    "skill_name": item["skill_name"],
                    "category": "mandatory" if idx < 5 else "preferred",
                    "skill_type": item["category"]
                }
                for idx, item in enumerate(extracted_job_skills)
            ]

        # Candidate details
        cand_exp_years = float(candidate_data.get("total_experience_years", 0.0))
        cand_edu_list = candidate_data.get("education", [])
        cand_skill_set = {s.lower() for s in candidate_skills}

        # ── 1. Technical Skill Match (40 Points) ───────────────────
        mandatory_reqs = [r for r in job_reqs if r.get("category") == "mandatory"]
        preferred_reqs = [r for r in job_reqs if r.get("category") != "mandatory"]

        # Default fallback if no requirements were tagged
        if not mandatory_reqs and not preferred_reqs:
            mandatory_reqs = job_reqs

        matched_skills: List[Dict[str, Any]] = []
        missing_skills: List[str] = []
        related_skills: List[str] = []

        total_weights = (len(mandatory_reqs) * 2) + len(preferred_reqs)
        earned_skill_points = 0.0

        for req in mandatory_reqs:
            s_name = req.get("skill_name", "")
            s_lower = s_name.lower()
            if s_lower in cand_skill_set:
                matched_skills.append({
                    "skill": s_name,
                    "type": "exact",
                    "evidence": f"Explicitly listed in verified technical competencies",
                    "confidence": 0.98,
                    "category": "mandatory"
                })
                earned_skill_points += 2.0
            else:
                # Check semantic / substring partial match
                is_partial = any(s_lower in c or c in s_lower for c in cand_skill_set)
                if is_partial:
                    related_skills.append(s_name)
                    matched_skills.append({
                        "skill": s_name,
                        "type": "related",
                        "evidence": f"Related competency identified in candidate skill profile",
                        "confidence": 0.75,
                        "category": "mandatory"
                    })
                    earned_skill_points += 1.2
                else:
                    missing_skills.append(s_name)

        for req in preferred_reqs:
            s_name = req.get("skill_name", "")
            s_lower = s_name.lower()
            if s_lower in cand_skill_set:
                matched_skills.append({
                    "skill": s_name,
                    "type": "exact",
                    "evidence": f"Candidate possesses preferred qualification",
                    "confidence": 0.95,
                    "category": "preferred"
                })
                earned_skill_points += 1.0
            else:
                is_partial = any(s_lower in c or c in s_lower for c in cand_skill_set)
                if is_partial:
                    related_skills.append(s_name)
                    matched_skills.append({
                        "skill": s_name,
                        "type": "related",
                        "evidence": f"Related secondary skill identified",
                        "confidence": 0.70,
                        "category": "preferred"
                    })
                    earned_skill_points += 0.6
                else:
                    missing_skills.append(f"{s_name} (preferred)")

        if total_weights > 0:
            tech_score = round(min(40.0, (earned_skill_points / total_weights) * 40.0), 1)
        else:
            tech_score = 30.0  # neutral default

        # ── 2. Semantic Similarity (30 Points) ─────────────────────
        # Construct summary of job requirements vs candidate profile text (excluding sensitive personal details like name)
        job_semantic_target = f"{job_title}. {job_description[:800]}"
        cand_semantic_doc = f"Candidate Profile. Experience: {cand_exp_years} years. Skills: {', '.join(candidate_skills)}. {resume_text[:1200]}"
        
        raw_similarity = self.embedding_service.compute_similarity(job_semantic_target, cand_semantic_doc)
        semantic_score = round(min(30.0, raw_similarity * 30.0), 1)

        # ── 3. Relevant Experience (20 Points) ─────────────────────
        if min_experience <= 0:
            exp_score = 20.0
        elif cand_exp_years >= min_experience:
            # Full score for meeting requirement, slight bonus for extra relevant years
            ratio = min(1.5, cand_exp_years / min_experience)
            exp_score = round(min(20.0, 18.0 + (ratio - 1.0) * 4.0), 1)
        else:
            # Proportional score
            ratio = cand_exp_years / min_experience
            exp_score = round(max(4.0, ratio * 20.0), 1)

        # ── 4. Education & Qualifications (10 Points) ──────────────
        edu_score = 8.0  # reasonable baseline
        cand_edu_text = str(cand_edu_list).lower()

        if "doctor" in cand_edu_text or "ph.d" in cand_edu_text or "phd" in cand_edu_text:
            edu_score = 10.0
        elif "master" in cand_edu_text or "m.s" in cand_edu_text or "m.tech" in cand_edu_text or "mba" in cand_edu_text:
            edu_score = 10.0 if "master" in education_req else 9.5
        elif "bachelor" in cand_edu_text or "b.s" in cand_edu_text or "b.tech" in cand_edu_text or "b.e" in cand_edu_text:
            edu_score = 10.0 if "bachelor" in education_req else 8.5
        elif cand_edu_list:
            edu_score = 7.5
        else:
            edu_score = 6.0  # missing education data is not penalized harshly

        # ── Overall Score (0 - 100 Points) ─────────────────────────
        overall_score = round(min(100.0, max(0.0, tech_score + semantic_score + exp_score + edu_score)), 1)

        # ── Candidate Strengths & Skill Gaps ───────────────────────
        strengths = []
        if tech_score >= 30.0:
            strengths.append(f"Strong technical alignment with {len(matched_skills)} verified required skills.")
        if cand_exp_years >= min_experience:
            strengths.append(f"Exceeds minimum experience requirement ({cand_exp_years} yrs vs {min_experience} yrs required).")
        if semantic_score >= 22.0:
            strengths.append("High contextual and domain semantic similarity with the job description.")
        if edu_score >= 9.0:
            strengths.append("Educational qualifications meet or exceed target job specifications.")
        if not strengths:
            strengths.append(f"Demonstrated background with {len(candidate_skills)} technical capabilities.")

        skill_gaps = []
        if missing_skills:
            key_missing = [s for s in missing_skills if not s.endswith("(preferred)")]
            if key_missing:
                skill_gaps.append(f"Missing mandatory requirements: {', '.join(key_missing[:4])}")
            pref_missing = [s for s in missing_skills if s.endswith("(preferred)")]
            if pref_missing:
                skill_gaps.append(f"Missing preferred skills: {', '.join(pref_missing[:3])}")
        if cand_exp_years < min_experience:
            diff = round(min_experience - cand_exp_years, 1)
            skill_gaps.append(f"Experience gap: {diff} year(s) below stated minimum ({min_experience} yrs).")
        if not skill_gaps:
            skill_gaps.append("No significant skill gaps identified for this role.")

        model_info = self.embedding_service.get_model_info()

        explanation = {
            "formula": "Overall (100) = Technical (40) + Semantic (30) + Experience (20) + Education (10)",
            "model_info": model_info,
            "technical_breakdown": {
                "score": tech_score,
                "max": 40.0,
                "earned_weight": round(earned_skill_points, 2),
                "total_weights": total_weights,
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills)
            },
            "semantic_breakdown": {
                "score": semantic_score,
                "max": 30.0,
                "cosine_similarity": round(raw_similarity, 4),
                "model": model_info["model_name"],
                "engine": model_info["engine"],
                "status": model_info["status"]
            },
            "experience_breakdown": {
                "score": exp_score,
                "max": 20.0,
                "candidate_years": cand_exp_years,
                "required_years": min_experience,
                "status": "Meets requirement" if cand_exp_years >= min_experience else "Below minimum"
            },
            "education_breakdown": {
                "score": edu_score,
                "max": 10.0,
                "required": education_req,
                "candidate_education": [e.get("degree", "Degree") for e in cand_edu_list] if cand_edu_list else ["Not specified"]
            }
        }

        return {
            "overall_score": overall_score,
            "technical_score": tech_score,
            "semantic_score": semantic_score,
            "experience_score": exp_score,
            "education_score": edu_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "related_skills": related_skills,
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "explanation": explanation,
            "model_info": model_info
        }

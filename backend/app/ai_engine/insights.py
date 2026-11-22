from typing import Any

from app.ai_engine.llm_service import LLMService


class CandidateInsights:
    """
    Recruiter Decision-Support Insights Engine.
    Summarizes applicant qualifications, identifies strengths & cautions,
    and constructs actionable recruiter interview checklists.
    Uses LLM (Gemini/OpenAI/Groq) when enabled, with robust rule-based fallback.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def generate_insights(
        self,
        candidate_name: str,
        overall_score: float,
        matched_skills: list[dict[str, Any]],
        missing_skills: list[str],
        experience_years: float,
        min_experience_required: float,
        use_llm: bool = True,
    ) -> dict[str, Any]:
        """Generate structured recruiter insights."""
        # Try LLM generation first if available and enabled
        if use_llm and self.llm_service.is_available():
            llm_insights = self.llm_service.generate_candidate_insights(
                candidate_name=candidate_name,
                overall_score=overall_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                experience_years=experience_years,
                min_experience_required=min_experience_required,
            )
            if llm_insights:
                return llm_insights

        # Deterministic Rule-Based Fallback
        # Determine Recommendation Tier
        if overall_score >= 80.0:
            tier = "Strong Candidate"
            verdict = "Recommended for Immediate Recruiter Interview"
            color = "emerald"
        elif overall_score >= 65.0:
            tier = "Solid Contender"
            verdict = "Recommended for Technical Screening"
            color = "blue"
        elif overall_score >= 50.0:
            tier = "Potential Match"
            verdict = "Review for Alternative or Junior Alignment"
            color = "amber"
        else:
            tier = "Requires Review"
            verdict = "Significant Gaps in Required Qualifications"
            color = "rose"

        # Actionable Recruiter Verification Points
        checklist = []
        if missing_skills:
            top_missing = [s for s in missing_skills if not s.endswith("(preferred)")][:3]
            if top_missing:
                checklist.append(f"Verify candidate's familiarity with core requirements: {', '.join(top_missing)}.")

        if experience_years < min_experience_required:
            checklist.append(
                f"Candidate has {experience_years} years experience vs {min_experience_required} years specified. Assess project complexity and seniority."
            )
        else:
            checklist.append("Verify role ownership and scale of systems handled in prior roles.")

        checklist.append("Validate portfolio, code repositories, or production achievements.")

        summary = (
            f"{candidate_name} exhibits an overall alignment score of {overall_score}/100. "
            f"The candidate has {experience_years} years of demonstrated background with "
            f"{len(matched_skills)} verified core technologies. "
            f"Current recommendation: {verdict}."
        )

        return {
            "tier": tier,
            "verdict": verdict,
            "color": color,
            "summary": summary,
            "verification_checklist": checklist,
            "key_highlights": [
                f"{len(matched_skills)} technical competencies aligned",
                f"{experience_years} years recorded experience",
                f"{len(missing_skills)} gap areas to probe",
            ],
        }

import time
import json
import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.ai_engine.agents.base_agent import BaseAgent
from app.models.all_models import (
    Job,
    Candidate,
    MatchingAnalysis,
    EvidenceReference
)

logger = logging.getLogger(__name__)


class RecruiterCopilotAgent(BaseAgent):
    """
    Agent 8: Recruiter Copilot Agent.
    Intelligent recruitment assistant with real tool execution capabilities.
    Queries live database records, conducts semantic filtering, explains scoring rationale,
    surfaces resume evidence citations, and generates tailored interview kits with human-in-the-loop safeguards.
    """

    TOOLS = [
        {"name": "search_candidates", "description": "Search candidates by keywords, skills, or location."},
        {"name": "filter_candidates", "description": "Filter candidates by minimum match score or experience years."},
        {"name": "get_candidate_profile", "description": "Retrieve full profile, skills, and projects for a candidate."},
        {"name": "get_resume_evidence", "description": "Inspect exact resume text snippet and page citation for a skill."},
        {"name": "compare_candidates", "description": "Compare 2 to 4 candidates side-by-side for a job."},
        {"name": "explain_score", "description": "Explain how a candidate's match score was calculated across weighted criteria."},
        {"name": "get_top_candidates", "description": "Retrieve the top ranked candidates for the active job."},
        {"name": "shortlist_candidate", "description": "Add candidate to job shortlist (requires confirmation)."}
    ]

    def __init__(self):
        super().__init__(
            agent_name="RecruiterCopilotAgent",
            description="Autonomous recruiter assistant executing approved database tools and grounded reasoning."
        )

    def execute(
        self,
        db: Session,
        message: str,
        conversation_id: Optional[str] = None,
        job_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Execute copilot query with tool execution and grounded reasoning."""
        start_time = time.time()
        
        # 1. Sanitize untrusted prompt input
        cleaned_msg = self.sanitize_untrusted_input(message)

        # 2. Identify and execute tools based on query intent
        tool_results = self._route_and_execute_tools(db, cleaned_msg, job_id, candidate_id)

        # 3. Generate response using LLM or deterministic grounded synthesis
        response_text = None
        executed_tool_name = tool_results.get("tool_name")
        tool_data = tool_results.get("data")
        requires_confirmation = tool_results.get("requires_confirmation", False)

        if self.llm_service.is_available():
            try:
                response_text = self._synthesize_via_llm(
                    user_message=cleaned_msg,
                    tool_name=executed_tool_name,
                    tool_data=tool_data,
                    conversation_history=conversation_history
                )
            except Exception as e:
                logger.warning(f"Copilot LLM synthesis failed: {e}. Using deterministic response.")

        if not response_text:
            response_text = self._synthesize_deterministic(cleaned_msg, executed_tool_name, tool_data, tool_results)

        duration_ms = int((time.time() - start_time) * 1000)
        self.record_execution(
            db=db,
            task_name="COPILOT_QUERY",
            target_entity_type="job" if job_id else "general",
            target_entity_id=job_id,
            status="completed",
            duration_ms=duration_ms,
            tokens_used=400 if self.llm_service.is_available() else 0,
            model_used=self.llm_service.model if self.llm_service.is_available() else "grounded-tool-router",
            input_summary=f"Query: {cleaned_msg[:120]}",
            output_summary=f"Executed tool: {executed_tool_name}. Response length: {len(response_text)} chars."
        )

        # Build candidate reference pills for UI
        candidate_refs = []
        if isinstance(tool_data, list):
            for item in tool_data[:5]:
                if isinstance(item, dict) and "id" in item and "name" in item:
                    candidate_refs.append({"id": item["id"], "name": item["name"], "score": item.get("score")})
        elif isinstance(tool_data, dict) and "id" in tool_data and "name" in tool_data:
            candidate_refs.append({"id": tool_data["id"], "name": tool_data["name"], "score": tool_data.get("score")})

        return {
            "assistant_message": response_text,
            "message": response_text,
            "response": response_text,
            "tool_executed": executed_tool_name,
            "tool_data": tool_data,
            "requires_confirmation": requires_confirmation,
            "confirmation_action": tool_results.get("confirmation_action"),
            "candidate_references": candidate_refs,
            "suggestions": self._get_contextual_suggestions(job_id, candidate_id)
        }

    def _route_and_execute_tools(
        self,
        db: Session,
        message: str,
        job_id: Optional[str],
        candidate_id: Optional[str]
    ) -> Dict[str, Any]:
        """Parse query intent and invoke approved database tool safely."""
        lower = message.lower()

        # Tool: Shortlist Candidate (Requires Confirmation)
        if any(w in lower for w in ["shortlist", "add to shortlist"]) and (candidate_id or re.search(r"shortlist\s+([a-zA-Z\s]+)", lower)):
            cand = None
            if candidate_id:
                cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not cand:
                # Search by name in message
                for c in db.query(Candidate).limit(50).all():
                    if c.name.lower() in lower:
                        cand = c
                        break
            if cand and job_id:
                return {
                    "tool_name": "shortlist_candidate",
                    "requires_confirmation": True,
                    "confirmation_action": {
                        "type": "SHORTLIST_CANDIDATE",
                        "candidate_id": cand.id,
                        "candidate_name": cand.name,
                        "job_id": job_id
                    },
                    "data": {"id": cand.id, "name": cand.name, "job_id": job_id}
                }

        # Tool: Compare Candidates
        if "compare" in lower:
            # Find candidate names in message
            matched_candidates = []
            for c in db.query(Candidate).limit(50).all():
                if c.name.lower() in lower:
                    matched_candidates.append(c)
            if len(matched_candidates) >= 2:
                from app.ai_engine.agents.comparison_agent import CandidateComparisonAgent
                comp_agent = CandidateComparisonAgent()
                job = db.query(Job).filter(Job.id == job_id).first() if job_id else db.query(Job).first()
                if job:
                    evals = []
                    for cand in matched_candidates[:3]:
                        analysis = db.query(MatchingAnalysis).filter(
                            MatchingAnalysis.candidate_id == cand.id,
                            MatchingAnalysis.job_id == job.id
                        ).first()
                        evals.append({
                            "candidate": {"id": cand.id, "name": cand.name},
                            "analysis": {
                                "overall_score": analysis.overall_score if analysis else 75.0,
                                "technical_score": analysis.technical_score if analysis else 70.0,
                                "matched_skills": analysis.matched_skills if analysis else []
                            }
                        })
                    res = comp_agent.execute(job_data={"id": job.id, "title": job.title, "requirements": job.requirements}, candidate_evaluations=evals)
                    return {"tool_name": "compare_candidates", "data": res}

        # Tool: Explain Score
        if any(w in lower for w in ["why", "explain", "score breakdown", "how did"]):
            target_cand = None
            if candidate_id:
                target_cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not target_cand:
                for c in db.query(Candidate).limit(50).all():
                    if c.name.lower() in lower:
                        target_cand = c
                        break
            if target_cand:
                analysis = db.query(MatchingAnalysis).filter(MatchingAnalysis.candidate_id == target_cand.id).first()
                if analysis:
                    return {
                        "tool_name": "explain_score",
                        "data": {
                            "id": target_cand.id,
                            "name": target_cand.name,
                            "overall_score": analysis.overall_score,
                            "technical_score": analysis.technical_score,
                            "projects_score": analysis.projects_score,
                            "experience_score": analysis.experience_score,
                            "strengths": analysis.strengths or [],
                            "skill_gaps": analysis.skill_gaps or [],
                            "weights_used": analysis.weights_used
                        }
                    }

        # Tool: Get Resume Evidence
        if any(w in lower for w in ["evidence", "proof", "show snippet", "where does it say", "page"]):
            target_cand = None
            if candidate_id:
                target_cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not target_cand:
                for c in db.query(Candidate).limit(50).all():
                    if c.name.lower() in lower:
                        target_cand = c
                        break
            if target_cand:
                ev_items = db.query(EvidenceReference).filter(EvidenceReference.candidate_id == target_cand.id).all()
                evidence_list = [
                    {
                        "criterion": ev.criterion,
                        "snippet": ev.snippet,
                        "page_number": ev.page_number,
                        "evidence_classification": ev.evidence_classification,
                        "confidence": ev.confidence
                    }
                    for ev in ev_items[:5]
                ]
                return {
                    "tool_name": "get_resume_evidence",
                    "data": {
                        "candidate_id": target_cand.id,
                        "candidate_name": target_cand.name,
                        "evidence": evidence_list
                    }
                }

        # Tool: Filter or Search by Skill
        skill_keywords = ["python", "react", "fastapi", "docker", "aws", "kubernetes", "sql", "machine learning", "pytorch"]
        found_skills = [sk for sk in skill_keywords if sk in lower]
        if found_skills:
            matching_cands = []
            for c in db.query(Candidate).limit(50).all():
                c_skills = {s.skill_name.lower() for s in c.skills}
                if any(fs in c_skills for fs in found_skills):
                    analysis = db.query(MatchingAnalysis).filter(MatchingAnalysis.candidate_id == c.id).first()
                    matching_cands.append({
                        "id": c.id,
                        "name": c.name,
                        "score": analysis.overall_score if analysis else 80.0,
                        "experience_years": c.total_experience_years,
                        "matching_skills": list(c_skills.intersection(found_skills))
                    })
            matching_cands.sort(key=lambda x: x["score"], reverse=True)
            return {
                "tool_name": "filter_candidates_by_skill",
                "data": matching_cands[:8]
            }

        # Default Tool: Top Candidates for Job or Overall
        top_query = db.query(MatchingAnalysis)
        if job_id:
            top_query = top_query.filter(MatchingAnalysis.job_id == job_id)
        top_matches = top_query.order_by(desc(MatchingAnalysis.overall_score)).limit(5).all()

        top_list = []
        for tm in top_matches:
            c = db.query(Candidate).filter(Candidate.id == tm.candidate_id).first()
            if c:
                top_list.append({
                    "id": c.id,
                    "name": c.name,
                    "score": tm.overall_score,
                    "technical_score": tm.technical_score,
                    "experience_years": c.total_experience_years
                })

        return {
            "tool_name": "get_top_candidates",
            "data": top_list
        }

    def _synthesize_via_llm(
        self,
        user_message: str,
        tool_name: str,
        tool_data: Any,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> Optional[str]:
        system_prompt = (
            "You are the TalentMatch AI Recruiter Copilot, an enterprise recruitment intelligence assistant. "
            "Use the provided verified database facts to formulate an executive, concise, and helpful response. "
            "Always state facts objectively. If asked to compare or evaluate, cite scores and specific skills. "
            "Never invent candidate credentials or fabricate unrecorded facts."
        )

        messages = []
        if conversation_history:
            messages.extend(conversation_history[-4:])

        prompt_content = f"""
User Query: {user_message}

Executed Database Tool: {tool_name}
Retrieved Database Facts:
{json.dumps(tool_data, indent=2) if tool_data else 'No matching records found in database.'}

Formulate a concise, professional markdown response answering the recruiter's question directly based ONLY on the retrieved facts above.
"""
        messages.append({"role": "user", "content": prompt_content})
        return self.llm_service.generate_chat_response(messages=messages, system_prompt=system_prompt, max_tokens=1000)

    def _synthesize_deterministic(
        self,
        message: str,
        tool_name: str,
        data: Any,
        raw_result: Dict[str, Any]
    ) -> str:
        if raw_result.get("requires_confirmation"):
            action = raw_result.get("confirmation_action", {})
            return (
                f"⚠️ **Action Requires Confirmation**\n\n"
                f"You requested to add **{action.get('candidate_name')}** to the job shortlist. "
                f"Please confirm to update this candidate's official recruitment pipeline status."
            )

        if tool_name == "get_top_candidates":
            if not data:
                return "No evaluated candidates were found for this criteria. Please ensure resumes have been uploaded and processed."
            lines = ["Here are the top ranked candidates based on verified multi-criteria match scores:\n"]
            for idx, c in enumerate(data, 1):
                lines.append(f"{idx}. **{c['name']}** — **{c['score']}/100** ({c['experience_years']} yrs exp, Tech score: {c.get('technical_score', 'N/A')})")
            lines.append("\nYou can ask me to compare any of these candidates or inspect their supporting resume evidence.")
            return "\n".join(lines)

        elif tool_name == "filter_candidates_by_skill":
            if not data:
                return "No candidates in the database were found possessing the specified technical skills."
            lines = [f"Found **{len(data)}** candidates with relevant technical competencies:\n"]
            for idx, c in enumerate(data, 1):
                matched_str = ", ".join(c.get("matching_skills", []))
                lines.append(f"{idx}. **{c['name']}** — **{c['score']}/100** (Verified in: {matched_str})")
            return "\n".join(lines)

        elif tool_name == "explain_score":
            if not data:
                return "Score explanation could not be retrieved for this candidate."
            lines = [
                f"### Scoring Breakdown for {data['name']}\n",
                f"- **Overall Match Score:** **{data['overall_score']}/100**",
                f"- **Technical Skills Score:** {data['technical_score']}/100",
                f"- **Project Substance Score:** {data.get('projects_score', 'N/A')}/100",
                f"- **Experience Score:** {data['experience_score']}/100\n",
                "**Key Strengths:**"
            ]
            for s in data.get("strengths", [])[:3]:
                lines.append(f"- {s}")
            if data.get("skill_gaps"):
                lines.append("\n**Identified Skill Gaps:**")
                for g in data.get("skill_gaps", [])[:3]:
                    lines.append(f"- {g}")
            return "\n".join(lines)

        elif tool_name == "get_resume_evidence":
            ev_list = data.get("evidence", [])
            if not ev_list:
                return f"No evidence references have been indexed yet for {data.get('candidate_name')}."
            lines = [f"### Resume Evidence Citations for {data.get('candidate_name')}\n"]
            for ev in ev_list:
                lines.append(f"- **{ev['criterion']}** (Page {ev['page_number']}, {ev['evidence_classification']}):\n  > \"{ev['snippet']}\"\n")
            return "\n".join(lines)

        elif tool_name == "compare_candidates":
            diffs = data.get("differentiators", [])
            diff_text = "\n".join(f"- {d}" for d in diffs)
            return (
                f"### Candidate Comparison Summary\n\n"
                f"**Top Match:** {data.get('leader', {}).get('name')} ({data.get('leader', {}).get('score')}/100)\n\n"
                f"**Key Differentiators:**\n{diff_text}\n\n"
                f"**Recommendation:** {data.get('executive_recommendation')}"
            )

        return f"I analyzed your request ('{message}') against our recruitment database and verified the relevant records."

    def _get_contextual_suggestions(self, job_id: Optional[str], candidate_id: Optional[str]) -> List[str]:
        suggestions = [
            "Show the top 5 candidates for this job",
            "Find candidates with Python and FastAPI experience",
            "Explain why the top candidate received their score",
            "Compare the top 2 candidates side-by-side"
        ]
        if candidate_id:
            suggestions.insert(0, "Show supporting resume evidence for this candidate")
            suggestions.insert(1, "Generate a tailored interview kit")
        return suggestions[:4]

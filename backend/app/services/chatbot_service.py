import logging
import uuid
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.ai_engine.llm_service import LLMService
from app.models.all_models import (
    Candidate,
    CandidateSkill,
    Job,
    JobRequirement,
    MatchingAnalysis,
    Resume,
    Shortlist,
    User,
)

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Intelligent Recruitment Copilot Service.
    Queries real application data and provides grounded answers via LLM,
    with an evidence-based deterministic fallback engine.
    """

    def __init__(self):
        self.llm_service = LLMService()
        self._conversations: dict[str, list[dict[str, str]]] = {}

    def get_conversation_history(self, conversation_id: str) -> list[dict[str, str]]:
        return self._conversations.get(conversation_id, [])

    def record_message(self, conversation_id: str, role: str, content: str):
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append({"role": role, "content": content})
        # Keep maximum 12 turns to stay responsive
        if len(self._conversations[conversation_id]) > 12:
            self._conversations[conversation_id] = self._conversations[conversation_id][-12:]

    def clear_conversation(self, conversation_id: str):
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

    def classify_intent(self, message: str) -> str:
        """Classify user query intent for recruitment assistance and safe boundary routing."""
        msg = message.lower().strip()
        if any(w in msg for w in ["malware", "virus", "exploit", "keylogger", "hack", "cookie", "recipe", "chocolate"]):
            return "out_of_scope"
        if any(w in msg for w in ["top", "rank", "leaderboard", "best candidate"]):
            return "ranking_query"
        if any(w in msg for w in ["score", "calculated", "formula", "algorithm", "why"]):
            return "score_explanation"
        if any(w in msg for w in ["shortlist"]):
            return "shortlist_query"
        if any(w in msg for w in ["interview", "question", "questions"]):
            return "interview_query"
        if any(w in msg for w in ["missing", "gap", "lacking"]):
            return "gap_analysis"
        if any(w in msg for w in ["compare", "comparison"]):
            return "comparison_query"
        if any(w in msg for w in ["upload", "resume", "cv"]):
            return "upload_query"
        if any(w in msg for w in ["dashboard", "stats", "analytics"]):
            return "stats_query"
        return "general_recruitment"

    _classify_intent = classify_intent

    def _fetch_ground_truth(
        self, db: Session, message: str, job_id: str | None = None, candidate_id: str | None = None
    ) -> dict[str, Any]:
        """Fetch real database facts relevant to user query."""
        facts: dict[str, Any] = {}

        # 1. Global Platform Stats
        facts["total_jobs"] = db.query(Job).count()
        facts["total_candidates"] = db.query(Candidate).count()
        facts["total_resumes"] = db.query(Resume).count()
        avg_s = db.query(func.avg(MatchingAnalysis.overall_score)).scalar()
        facts["avg_matching_score"] = round(float(avg_s), 1) if avg_s else 0.0
        facts["shortlisted_count"] = db.query(Shortlist).filter(Shortlist.status == "shortlisted").count()

        # 2. Job Context
        target_job = None
        if job_id:
            target_job = db.query(Job).filter(Job.id == job_id).first()
        if not target_job:
            # Check if any job title is mentioned in message
            all_jobs = db.query(Job).limit(10).all()
            for j in all_jobs:
                if j.title.lower() in message.lower():
                    target_job = j
                    break
        if not target_job:
            # Default to the most active/recent job
            target_job = db.query(Job).order_by(Job.created_at.desc()).first()

        if target_job:
            reqs = db.query(JobRequirement).filter(JobRequirement.job_id == target_job.id).all()
            mandatory = [r.skill_name for r in reqs if r.category == "mandatory"]
            preferred = [r.skill_name for r in reqs if r.category == "preferred"]
            facts["active_job"] = {
                "id": target_job.id,
                "title": target_job.title,
                "company": target_job.company,
                "min_experience": target_job.min_experience,
                "education_req": target_job.education_req,
                "mandatory_skills": mandatory,
                "preferred_skills": preferred,
            }

        # 3. Candidate Context
        target_candidate = None
        if candidate_id:
            target_candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not target_candidate:
            # Check if any candidate name is mentioned in user message
            candidates_all = db.query(Candidate).limit(50).all()
            for c in candidates_all:
                if c.name.lower() in message.lower():
                    target_candidate = c
                    break

        if target_candidate:
            skills = (
                db.query(CandidateSkill.skill_name).filter(CandidateSkill.candidate_id == target_candidate.id).all()
            )
            # Fetch match analysis if exists
            match_analysis = None
            if target_job:
                match_analysis = (
                    db.query(MatchingAnalysis)
                    .filter(
                        MatchingAnalysis.candidate_id == target_candidate.id, MatchingAnalysis.job_id == target_job.id
                    )
                    .first()
                )
            if not match_analysis:
                match_analysis = (
                    db.query(MatchingAnalysis)
                    .filter(MatchingAnalysis.candidate_id == target_candidate.id)
                    .order_by(MatchingAnalysis.overall_score.desc())
                    .first()
                )

            facts["target_candidate"] = {
                "id": target_candidate.id,
                "name": target_candidate.name,
                "experience_years": target_candidate.total_experience_years,
                "skills": [s[0] for s in skills[:15]],
                "score": match_analysis.overall_score if match_analysis else None,
                "technical_score": match_analysis.technical_score if match_analysis else None,
                "semantic_score": match_analysis.semantic_score if match_analysis else None,
                "experience_score": match_analysis.experience_score if match_analysis else None,
                "education_score": match_analysis.education_score if match_analysis else None,
                "strengths": match_analysis.strengths if match_analysis else [],
                "skill_gaps": match_analysis.skill_gaps if match_analysis else [],
                "missing_skills": match_analysis.missing_skills if match_analysis else [],
            }

        # 4. Top Ranked Candidates for current job or overall
        top_query = db.query(MatchingAnalysis)
        if target_job:
            top_query = top_query.filter(MatchingAnalysis.job_id == target_job.id)
        top_matches = top_query.order_by(desc(MatchingAnalysis.overall_score)).limit(5).all()

        top_list = []
        for tm in top_matches:
            c = db.query(Candidate).filter(Candidate.id == tm.candidate_id).first()
            if c:
                top_list.append(
                    {
                        "candidate_id": c.id,
                        "name": c.name,
                        "score": round(tm.overall_score, 1),
                        "experience_years": c.total_experience_years,
                        "strengths": tm.strengths[:2],
                        "skill_gaps": tm.skill_gaps[:2],
                    }
                )
        facts["top_candidates"] = top_list

        return facts

    def _generate_fallback_response(self, message: str, facts: dict[str, Any]) -> dict[str, Any]:
        """Evidence-based deterministic response when LLM is unavailable or quota limited."""
        msg = message.lower().strip()
        job = facts.get("active_job")
        top_cands = facts.get("top_candidates", [])
        target_c = facts.get("target_candidate")

        # 1. Scoring & Matching Calculation
        if "score" in msg or "calculated" in msg or "formula" in msg or "algorithm" in msg:
            text = (
                "### 🎯 How TalentMatch AI Computes Candidate Match Scores\n\n"
                "TalentMatch AI uses an **evidence-based 4-component weighted scoring algorithm (0 – 100 points)**:\n\n"
                "1. **Technical Skill Alignment (40%)**: Compares verified candidate skills against mandatory and preferred job requirements.\n"
                "2. **Semantic Similarity (30%)**: Uses transformer document embeddings (`all-MiniLM-L6-v2`) with cosine similarity to evaluate resume context against job responsibilities.\n"
                "3. **Relevant Experience (20%)**: Mathematically scales demonstrated candidate experience against the job's minimum required years.\n"
                "4. **Education & Qualifications (10%)**: Compares degree attainment level (Ph.D., Master's, Bachelor's) to job criteria.\n\n"
                "> All scores are 100% explainable—surfacing matched skills, identified gaps, and contextual evidence without black-box bias."
            )
            return {
                "message": text,
                "suggestions": [
                    "Show me the top-ranked candidates.",
                    "What are the missing skills for a candidate?",
                    "Explain the recruitment dashboard.",
                ],
            }

        # 2. Top-ranked candidates
        if "top" in msg or "best candidate" in msg or "rank" in msg or "leaderboard" in msg:
            job_title = job.get("title") if job else "Active Job Openings"
            if not top_cands:
                text = f"Currently, no candidate match analyses are recorded for **{job_title}**. Please run AI Matching from the **AI Matching** page."
            else:
                lines = [f"### 🏆 Top-Ranked Candidates for **{job_title}**\n"]
                for i, c in enumerate(top_cands, 1):
                    lines.append(
                        f"**{i}. {c['name']}** — **{c['score']}/100** ({c['experience_years']} yrs exp)\n"
                        f"   - **Strengths:** {', '.join(c['strengths']) if c['strengths'] else 'Strong profile alignment'}\n"
                        f"   - **Skill Gaps:** {', '.join(c['skill_gaps']) if c['skill_gaps'] else 'None identified'}"
                    )
                lines.append(
                    "\n*Click on any candidate name or view the **Candidate Ranking** page to inspect full profiles and export reports.*"
                )
                text = "\n".join(lines)
            return {
                "message": text,
                "suggestions": [
                    "Compare the top two candidates.",
                    "What are the missing skills for a candidate?",
                    "How does candidate score work?",
                ],
            }

        # 3. Missing skills or skill gaps
        if "missing" in msg or "gap" in msg or "lacking" in msg:
            cand = target_c or (top_cands[0] if top_cands else None)
            if cand and isinstance(cand, dict):
                c_name = cand.get("name", "Candidate")
                gaps = cand.get("skill_gaps", []) or cand.get("missing_skills", [])
                text = (
                    f"### 🔍 Skill Gap Analysis for **{c_name}**\n\n"
                    f"Based on the job requirements for **{job.get('title') if job else 'the target position'}**:\n\n"
                )
                if gaps:
                    for g in gaps:
                        text += f"- ⚠️ **{g}**: Missing or unverified in applicant resume.\n"
                    text += "\n**Recruiter Recommendation:** Probe these areas during the technical screen or ask about adjacent frameworks."
                else:
                    text += "✅ This candidate has verified coverage for all core mandatory skills specified in the job description."
            else:
                text = "Please select a candidate or run an AI match first to analyze missing skill gaps."
            return {
                "message": text,
                "suggestions": [
                    "Show me the top-ranked candidates.",
                    "How can I compare candidates?",
                    "How does AI resume matching work?",
                ],
            }

        # 4. Compare candidates
        if "compare" in msg or "comparison" in msg:
            if len(top_cands) >= 2:
                c1, c2 = top_cands[0], top_cands[1]
                text = (
                    f"### ⚖️ Side-by-Side Comparison: **{c1['name']}** vs **{c2['name']}**\n\n"
                    f"| Metric | **{c1['name']}** | **{c2['name']}** |\n"
                    f"|---|---|---|\n"
                    f"| **Overall Match Score** | **{c1['score']}/100** | **{c2['score']}/100** |\n"
                    f"| **Experience** | {c1['experience_years']} Years | {c2['experience_years']} Years |\n"
                    f"| **Key Strengths** | {', '.join(c1['strengths'])} | {', '.join(c2['strengths'])} |\n"
                    f"| **Identified Gaps** | {', '.join(c1['skill_gaps'])} | {', '.join(c2['skill_gaps'])} |\n\n"
                    f"💡 Navigate to the **Compare Candidates** page in the left sidebar to add more candidates to a full multi-dimensional matrix."
                )
            else:
                text = "To compare candidates, please ensure at least two candidates have been evaluated under the current job description."
            return {
                "message": text,
                "suggestions": [
                    "Show me the top-ranked candidates.",
                    "How is the candidate score calculated?",
                    "Explain the recruitment dashboard.",
                ],
            }

        # 5. Upload multiple resumes
        if "upload" in msg or "bulk" in msg or "resume" in msg and ("how" in msg or "multiple" in msg):
            text = (
                "### 📄 How to Bulk Upload Resumes in TalentMatch AI\n\n"
                "1. Click **Resume Upload** in the left sidebar navigation.\n"
                "2. Drag and drop **10 to 50 resumes** at once (supported formats: **.PDF, .DOCX, .TXT**, max 15MB each).\n"
                "3. Alternatively, click the **'Load 15 Demo Resumes'** button for an instant demo batch.\n"
                "4. The system validates document headers, checks for duplicate hashes, extracts candidate details and technical skills, and creates normalized candidate profiles automatically.\n"
                "5. Once uploaded, head over to **AI Matching** to pair them against any active job!"
            )
            return {
                "message": text,
                "suggestions": [
                    "How does AI resume matching work?",
                    "Show me the top-ranked candidates.",
                    "Explain the recruitment dashboard.",
                ],
            }

        # 6. Recruitment dashboard & stats
        if "dashboard" in msg or "stats" in msg or "statistic" in msg or "analytics" in msg or "how many" in msg:
            text = (
                "### 📊 TalentMatch AI Recruitment Dashboard Overview\n\n"
                f"Here is your current live platform snapshot:\n\n"
                f"- **Active Job Positions:** `{facts.get('total_jobs', 0)}`\n"
                f"- **Ingested Resumes:** `{facts.get('total_resumes', 0)}`\n"
                f"- **Candidate Profiles:** `{facts.get('total_candidates', 0)}`\n"
                f"- **Average Match Score:** `{facts.get('avg_matching_score', 0.0)}/100`\n"
                f"- **Shortlisted Applicants:** `{facts.get('shortlisted_count', 0)}`\n\n"
                "The dashboard visualizes candidate score distribution curves, skill availability histograms, recent recruiter activity logs, and quick actions to streamline talent acquisition."
            )
            return {
                "message": text,
                "suggestions": [
                    "Show me the top-ranked candidates.",
                    "How is the candidate score calculated?",
                    "Compare the top two candidates.",
                ],
            }

        # 7. General Welcome / Platform Help
        text = (
            f"Hello! I am your **TalentMatch AI Assistant**.\n\n"
            f"Currently managing **{facts.get('total_candidates', 0)} candidates** across **{facts.get('total_jobs', 0)} job openings** with an average score of **{facts.get('avg_matching_score', 0.0)}/100**.\n\n"
            "I can assist you with:\n"
            "- **Candidate Rankings & Shortlisting**: Finding top fits and inspecting score breakdowns.\n"
            "- **Skill Gap Analysis**: Highlighting missing mandatory vs. preferred requirements.\n"
            "- **Candidate Comparison**: Evaluating applicants side-by-side.\n"
            "- **Interview Preparation**: Generating tailored technical and behavioral questions.\n"
            "- **Platform Guidance**: Step-by-step help with bulk resume ingestion and report exports."
        )
        return {
            "message": text,
            "suggestions": [
                "How does AI resume matching work?",
                "How is the candidate score calculated?",
                "Show me the top-ranked candidates.",
                "What are the missing skills for a candidate?",
                "How do I upload multiple resumes?",
                "How can I compare candidates?",
                "Explain the recruitment dashboard.",
            ],
        }

    def chat(
        self,
        db: Session,
        message: str,
        conversation_id: str | None = None,
        job_id: str | None = None,
        candidate_id: str | None = None,
        page_context: str | None = None,
        user: User | None = None,
    ) -> dict[str, Any]:
        """Process chat message and return intelligent response."""
        cid = conversation_id or str(uuid.uuid4())
        self.record_message(cid, "user", message)

        facts = self._fetch_ground_truth(db, message, job_id, candidate_id)

        # Build LLM system prompt if LLM is available
        llm_response = None
        mode = "fallback"

        if self.llm_service.is_available():
            system_prompt = f"""
You are the "TalentMatch AI Assistant", an executive talent acquisition and AI recruitment copilot for AVOM Consultants.
Your goal is to help recruiters evaluate candidate resumes, explain matching algorithms, summarize applicant profiles, and navigate TalentMatch AI.

CURRENT LIVE RECRUITMENT DATABASE FACTS (Ground Truth):
- Total Jobs: {facts.get("total_jobs")}
- Total Resumes Uploaded: {facts.get("total_resumes")}
- Total Candidate Profiles: {facts.get("total_candidates")}
- Platform Average Match Score: {facts.get("avg_matching_score")}/100
- Total Shortlisted Candidates: {facts.get("shortlisted_count")}
- Current Job Context: {facts.get("active_job")}
- Selected Candidate Context: {facts.get("target_candidate")}
- Current Top Candidates: {facts.get("top_candidates")}
- Recruiter Page Context: {page_context or "Platform General"}
- Current Authenticated User: {user.full_name if user else "Recruiter"}

CRITICAL OPERATIONAL RULES:
1. Ground Truth Only: ALWAYS use the real database numbers, candidate names, and scores provided above. NEVER fabricate candidate names, jobs, or scores.
2. If data is not found or empty, clearly state: "There are currently no records found for this query in the database."
3. Ethical Recruitment: NEVER evaluate candidates based on age, gender, race, religion, nationality, marital status, or photographs.
4. Decision Support: You provide transparent data and analytical guidance to assist human recruiters. You NEVER make autonomous hiring decisions or auto-rejections.
5. 4-Component Scoring Model:
   - Technical Skills: 40%
   - Semantic Document Similarity (Transformers): 30%
   - Experience Duration: 20%
   - Education Alignment: 10%
6. Formatting: Use concise, professional markdown with bullet points, bold highlights, and tables where appropriate.
"""
            messages = self.get_conversation_history(cid)
            llm_text = self.llm_service.generate_chat_response(messages, system_prompt, max_tokens=1500)
            if llm_text:
                llm_response = llm_text
                mode = "llm"

        if llm_response:
            final_message = llm_response
            suggestions = [
                "Show me the top-ranked candidates.",
                "How is the candidate score calculated?",
                "What are the missing skills for a candidate?",
                "How can I compare candidates?",
            ]
        else:
            # Deterministic Fallback Engine
            fb = self._generate_fallback_response(message, facts)
            final_message = fb["message"]
            suggestions = fb.get("suggestions", [])
            mode = "fallback"

        self.record_message(cid, "assistant", final_message)

        return {
            "assistant_message": final_message,
            "conversation_id": cid,
            "relevant_data": {
                "active_job": facts.get("active_job"),
                "target_candidate": facts.get("target_candidate"),
                "top_candidates": facts.get("top_candidates", [])[:3],
                "stats": {
                    "total_jobs": facts.get("total_jobs"),
                    "total_resumes": facts.get("total_resumes"),
                    "total_candidates": facts.get("total_candidates"),
                },
            },
            "suggestions": suggestions,
            "mode": mode,
        }

    def generate_welcome_message(
        self,
        db: Session,
        user: User | None = None,
        page_context: str | None = None,
        job_id: str | None = None,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a dynamic, non-static, context-aware welcome message based on recruiter identity,
        current time of day, active page route, and live recruitment database metrics.
        """
        from datetime import datetime

        now = datetime.now()
        hour = now.hour
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        # User personalization
        user_name = None
        if user and user.full_name:
            user_name = user.full_name.strip().split()[0]
        elif user and user.email:
            user_name = user.email.split("@")[0].capitalize()
        else:
            user_name = "Alex"

        salutation = f"{time_greeting}, {user_name}!"

        # Live Database Metrics
        total_jobs = db.query(Job).count()
        total_candidates = db.query(Candidate).count()
        total_resumes = db.query(Resume).count()
        avg_score_scalar = db.query(func.avg(MatchingAnalysis.overall_score)).scalar()
        avg_score = round(float(avg_score_scalar), 1) if avg_score_scalar else 0.0
        shortlisted_count = db.query(Shortlist).filter(Shortlist.status == "shortlisted").count()

        # Simple, clean, live dynamic welcome message
        full_message = (
            f"{salutation} I'm your TalentMatch AI Copilot, connected live to your recruitment database. "
            f"Currently tracking {total_jobs} active jobs and {total_candidates} candidates "
            f"(platform average match: {avg_score}%). "
            "I can assist with resume analysis, explain scoring algorithms, highlight top candidates, or answer platform questions.\n\n"
            "How can I assist your recruitment workflow today?"
        )

        return {
            "welcome_message": full_message,
            "timestamp": now.strftime("%I:%M %p"),
            "mode": "dynamic",
            "stats": {
                "total_jobs": total_jobs,
                "total_candidates": total_candidates,
                "total_resumes": total_resumes,
                "avg_score": avg_score,
                "shortlisted_count": shortlisted_count,
            },
        }

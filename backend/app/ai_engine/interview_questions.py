from typing import List, Dict, Any
from app.ai_engine.llm_service import LLMService


class InterviewQuestionGenerator:
    """
    Intelligent technical interview question generator based on candidate profile,
    job description, matched skills, and unverified requirements.
    Uses LLM (Gemini/OpenAI/Groq) when enabled, with robust rule-based fallback.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def generate_questions(
        self,
        job_title: str,
        matched_skills: List[str],
        missing_skills: List[str],
        experience_years: float,
        candidate_projects: List[Dict[str, Any]],
        use_llm: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate structured technical, coding, project, and experience questions.
        """
        # Try LLM generation first if available and enabled
        if use_llm and self.llm_service.is_available():
            llm_questions = self.llm_service.generate_interview_questions(
                job_title=job_title,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                experience_years=experience_years,
                candidate_projects=candidate_projects
            )
            if llm_questions:
                return llm_questions

        # Deterministic Rule-Based Fallback
        questions = []

        # 1. Technical Deep-Dive Questions (based on top matched skills)
        primary_skills = matched_skills[:3]
        for skill in primary_skills:
            clean_s = skill.split("(")[0].strip()
            q_obj = self._get_skill_question(clean_s, job_title)
            if q_obj:
                questions.append(q_obj)

        # 2. Skill-Gap / Verification Question (based on missing skills)
        if missing_skills:
            gap_skill = missing_skills[0].split("(")[0].strip()
            questions.append({
                "type": "Skill Gap Verification",
                "skill": gap_skill,
                "question": f"The job requires hands-on experience with {gap_skill}. Have you worked with {gap_skill} or comparable alternatives in any recent engagements?",
                "evaluation_criteria": f"Look for conceptual understanding, transfer of knowledge from similar tools, or self-directed learning.",
                "difficulty": "Intermediate"
            })

        # 3. Practical Coding / System Design Scenario
        questions.append({
            "type": "Architecture & System Design",
            "skill": "System Design",
            "question": f"For a production system in {job_title}, how would you architect high availability, handle database connection bottlenecks, and implement zero-downtime deployments?",
            "evaluation_criteria": "Evaluates understanding of caching, connection pooling, horizontal scaling, and CI/CD best practices.",
            "difficulty": "Senior" if experience_years >= 4.0 else "Intermediate"
        })

        # 4. Project-Based Scenario
        if candidate_projects:
            proj_name = candidate_projects[0].get("name", "your recent project")
            questions.append({
                "type": "Project Deep-Dive",
                "skill": "Technical Delivery",
                "question": f"In {proj_name}, what was the most complex technical hurdle you encountered, and what architectural trade-offs did you make to resolve it?",
                "evaluation_criteria": "Candidate should articulate root cause, alternative options considered, and measurable business/performance outcome.",
                "difficulty": "Advanced"
            })
        else:
            questions.append({
                "type": "Experience & Behavioral",
                "skill": "Problem Solving",
                "question": "Can you describe a challenging production outage or critical bug you resolved under tight deadlines? What steps did you take to troubleshoot and prevent recurrence?",
                "evaluation_criteria": "Structured debugging methodology, observability tooling usage, and post-mortem mindset.",
                "difficulty": "Medium"
            })

        return questions

    def _get_skill_question(self, skill: str, job_title: str) -> Dict[str, Any]:
        """Lookup tailored questions for common technologies."""
        s = skill.lower()
        if "python" in s:
            return {
                "type": "Core Technical",
                "skill": "Python",
                "question": "Explain Python's memory management, the Global Interpreter Lock (GIL), and when you would prefer asyncio versus multiprocessing for concurrent workloads.",
                "evaluation_criteria": "Understands reference counting, garbage collection, async event loop vs CPU-bound multiprocessing.",
                "difficulty": "Advanced"
            }
        elif "react" in s:
            return {
                "type": "Core Technical",
                "skill": "React",
                "question": "How does React 18/19 handle concurrent rendering, and what strategies do you employ to prevent unnecessary component re-renders in large state trees?",
                "evaluation_criteria": "Demonstrates knowledge of Fiber reconciler, memoization (useMemo/useCallback), and state colocation.",
                "difficulty": "Advanced"
            }
        elif "fastapi" in s:
            return {
                "type": "Core Technical",
                "skill": "FastAPI",
                "question": "How do FastAPI dependency injection, Pydantic data validation, and asynchronous route execution work under ASGI?",
                "evaluation_criteria": "Articulates async def vs def threadpool handling, Starlette underpinning, and reusable Depends scopes.",
                "difficulty": "Intermediate"
            }
        elif "sql" in s or "postgres" in s:
            return {
                "type": "Database & Query Optimization",
                "skill": "PostgreSQL / SQL",
                "question": "How do you diagnose and optimize a slow query in PostgreSQL? Explain EXPLAIN ANALYZE, index selection (B-tree, GIN), and vacuuming.",
                "evaluation_criteria": "Understands query execution plans, index scans vs sequential scans, and table bloat.",
                "difficulty": "Advanced"
            }
        elif "docker" in s or "kubernetes" in s:
            return {
                "type": "DevOps & Cloud",
                "skill": "Containers / Kubernetes",
                "question": "How do you configure resource limits, health probes (liveness/readiness), and secure multi-stage container builds in Kubernetes?",
                "evaluation_criteria": "Awareness of OOM kills, rolling update readiness gates, and non-root user security.",
                "difficulty": "Intermediate"
            }
        else:
            return {
                "type": "Core Technical",
                "skill": skill,
                "question": f"Describe your practical experience using {skill}. What are its primary advantages and common pitfalls in an enterprise application?",
                "evaluation_criteria": f"Depth of hands-on experience and familiarity with {skill} best practices.",
                "difficulty": "Intermediate"
            }

import time
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.ai_engine.agents.base_agent import BaseAgent
from app.models.all_models import InterviewKit, generate_uuid, utc_now

logger = logging.getLogger(__name__)


class InterviewIntelligenceAgent(BaseAgent):
    """
    Agent 7: Interview Intelligence Agent.
    Generates personalized, structured interview kits tailored to the candidate's exact
    resume evidence and the job description requirements.
    Produces technical questions, project deep-dives, practical coding/architecture scenarios,
    claim verification probes, expected answer indicators, and 5-tier evaluation rubrics.
    """

    def __init__(self):
        super().__init__(
            agent_name="InterviewIntelligenceAgent",
            description="Generates evidence-backed technical questions, project deep-dives, claim-verification probes, and structured rubrics."
        )

    def execute(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        matched_skills: List[str],
        missing_skills: List[str],
        db: Optional[Session] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """Generate structured interview kit with LLM or deterministic fallback."""
        start_time = time.time()
        
        cand_id = candidate_data.get("id") or candidate_data.get("candidate_id", "unknown")
        job_id = job_data.get("id", "unknown")
        cand_name = candidate_data.get("name", "Candidate")
        job_title = job_data.get("title", "Software Engineer")
        projects = candidate_data.get("projects", [])
        exp_years = float(candidate_data.get("total_experience_years", 0.0))

        # Check existing interview kit in DB if available
        if db and cand_id != "unknown" and job_id != "unknown" and not candidate_data.get("force_regenerate"):
            existing = db.query(InterviewKit).filter(
                InterviewKit.candidate_id == cand_id,
                InterviewKit.job_id == job_id
            ).first()
            if existing:
                return {
                    "id": existing.id,
                    "candidate_id": cand_id,
                    "job_id": job_id,
                    "candidate_name": cand_name,
                    "job_title": job_title,
                    "questions": existing.questions,
                    "rubric_guidelines": existing.rubric_guidelines,
                    "evaluation_notes": existing.evaluation_notes,
                    "status": existing.status,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None
                }

        # 1. Attempt LLM generation
        questions = None
        if self.llm_service.is_available():
            try:
                questions = self._generate_via_llm(
                    job_title=job_title,
                    cand_name=cand_name,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    projects=projects,
                    exp_years=exp_years
                )
            except Exception as e:
                logger.warning(f"InterviewAgent LLM generation failed: {e}. Falling back to deterministic rubric engine.")

        # 2. Deterministic Fallback if LLM unavailable
        if not questions:
            questions = self._generate_deterministic(
                job_title=job_title,
                cand_name=cand_name,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                projects=projects,
                exp_years=exp_years
            )

        rubric_guidelines = {
            "scale": "1 to 5 (1=Unsatisfactory, 3=Competent, 5=Mastery)",
            "rubric_dimensions": [
                "Technical Accuracy & Depth",
                "Practical Problem-Solving Approach",
                "Communication & Architectural Reasoning",
                "Factual Consistency with Resume Claims"
            ]
        }

        # 3. Persist to database if requested
        kit_id = generate_uuid()
        if db and save_to_db and cand_id != "unknown" and job_id != "unknown":
            try:
                kit_record = InterviewKit(
                    id=kit_id,
                    candidate_id=cand_id,
                    job_id=job_id,
                    questions=questions,
                    rubric_guidelines=rubric_guidelines,
                    status="ready",
                    created_at=utc_now()
                )
                db.add(kit_record)
                db.commit()
                db.refresh(kit_record)
                kit_id = kit_record.id
            except Exception as e:
                logger.warning(f"Could not persist interview kit to DB: {e}")
                db.rollback()

        duration_ms = int((time.time() - start_time) * 1000)
        self.record_execution(
            db=db,
            task_name="GENERATE_INTERVIEW_KIT",
            target_entity_type="candidate",
            target_entity_id=cand_id,
            status="completed",
            duration_ms=duration_ms,
            tokens_used=600 if self.llm_service.is_available() else 0,
            model_used=self.llm_service.model if self.llm_service.is_available() else "deterministic-rubric-engine",
            input_summary=f"Generated kit for {cand_name} applying for {job_title}.",
            output_summary=f"Created {len(questions)} structured interview questions with rubrics."
        )

        return {
            "id": kit_id,
            "candidate_id": cand_id,
            "job_id": job_id,
            "candidate_name": cand_name,
            "job_title": job_title,
            "questions": questions,
            "rubric_guidelines": rubric_guidelines,
            "evaluation_notes": f"Generated based on {len(matched_skills)} verified skills and {len(projects)} resume projects.",
            "status": "ready",
            "created_at": utc_now()
        }

    def _generate_via_llm(
        self,
        job_title: str,
        cand_name: str,
        matched_skills: List[str],
        missing_skills: List[str],
        projects: List[Dict[str, Any]],
        exp_years: float
    ) -> Optional[List[Dict[str, Any]]]:
        prompt = f"""
You are the Interview Intelligence Agent for an enterprise recruitment platform.
Generate 5 structured interview questions tailored to {cand_name} applying for '{job_title}'.

Candidate Context:
- Experience: {exp_years} years
- Verified Skills: {', '.join(matched_skills[:6])}
- Missing/Unverified Skills: {', '.join(missing_skills[:4]) if missing_skills else 'None'}
- Projects: {json.dumps(projects[:2]) if projects else 'Standard software development projects'}

Include:
1. One Core Technical Question (in-depth on verified skill)
2. One Project Deep-Dive Question (specifically naming one of their projects)
3. One Practical Coding/Architecture Scenario (real-world system design for {job_title})
4. One Claim-Verification Question (probing an unverified skill or depth of claimed responsibility)
5. One Behavioral/Delivery Question (incident resolution, trade-offs, or teamwork)

Return a JSON array of objects under "questions" with this schema:
{{
  "questions": [
    {{
      "id": "q1",
      "category": "technical",
      "question": "<Question text>",
      "rationale": "<Why this question is relevant to the JD and candidate>",
      "expected_answer": "<Key signals and technical points a competent candidate must provide>",
      "rubric_levels": {{
        "1": "<Indicators of poor response>",
        "3": "<Indicators of solid acceptable response>",
        "5": "<Indicators of exceptional mastery>"
      }},
      "follow_up_probes": ["<Follow-up probe 1>", "<Follow-up probe 2>"]
    }}
  ]
}}
"""
        res = self.llm_service.generate_json(prompt)
        if res and isinstance(res, dict) and "questions" in res:
            return res["questions"]
        return None

    def _generate_deterministic(
        self,
        job_title: str,
        cand_name: str,
        matched_skills: List[str],
        missing_skills: List[str],
        projects: List[Dict[str, Any]],
        exp_years: float
    ) -> List[Dict[str, Any]]:
        primary_skill = matched_skills[0] if matched_skills else "Python"
        secondary_skill = matched_skills[1] if len(matched_skills) > 1 else "REST APIs"
        missing_skill = missing_skills[0] if missing_skills else "distributed caching"
        project_title = projects[0].get("title", "their primary project") if projects else "their most complex technical project"

        return [
            {
                "id": "q1",
                "category": "technical",
                "question": f"In your work with {primary_skill}, how do you structure production applications for high reliability, concurrency, and performance?",
                "rationale": f"Validates core technical depth in {primary_skill}, which is a mandatory requirement for {job_title}.",
                "expected_answer": f"Candidate should discuss memory management, asynchronous execution, proper error handling, testing frameworks, and profiling in {primary_skill}.",
                "rubric_levels": {
                    "1": f"Superficial syntax knowledge; struggles to explain production bottlenecks in {primary_skill}.",
                    "3": f"Solid familiarity with standard libraries, design patterns, and deployment configurations.",
                    "5": f"Deep architectural mastery; explains memory internals, concurrency models, and low-level optimization strategies."
                },
                "follow_up_probes": [
                    f"What was the most challenging bug you diagnosed when working with {primary_skill}?",
                    "How do you monitor and debug unexpected latency spikes in production?"
                ]
            },
            {
                "id": "q2",
                "category": "project",
                "question": f"Walk us through the architecture of {project_title}. What were the key technical trade-offs you made during design and delivery?",
                "rationale": "Verifies genuine ownership and practical delivery capability claimed on the resume.",
                "expected_answer": "Candidate should articulate clear component boundaries, database selection reasoning, failure mode handling, and measurable outcomes.",
                "rubric_levels": {
                    "1": "Generic overview without technical specifics; unable to explain architectural trade-offs.",
                    "3": "Clear explanation of system layers, database interactions, and individual contributions.",
                    "5": "Exceptional system clarity; details scaling limits, security choices, and what they would re-architect today."
                },
                "follow_up_probes": [
                    "If user traffic or data volume multiplied by 100x overnight, where would this system break first?",
                    "What automated tests or CI/CD steps protected this system from regressions?"
                ]
            },
            {
                "id": "q3",
                "category": "coding_architecture",
                "question": f"Design an idempotent API endpoint for {job_title} that handles concurrent transaction requests without data corruption or duplicate processing.",
                "rationale": "Tests practical production engineering discipline and defensive API design.",
                "expected_answer": "Candidate must mention unique idempotency keys, database row-level locking or optimistic concurrency, atomicity (ACID), and distributed locks or caching.",
                "rubric_levels": {
                    "1": "Fails to grasp race conditions or concurrent state conflicts.",
                    "3": "Implements unique tokens and database transactions correctly.",
                    "5": "Comprehensive design covering distributed locking (Redis Redlock), idempotency persistence, replay protection, and rollback."
                },
                "follow_up_probes": [
                    "How do you handle client retries when the backend operation succeeded but the network timed out?",
                    "What HTTP status codes and headers would your API return for duplicate requests?"
                ]
            },
            {
                "id": "q4",
                "category": "claim_verification",
                "question": f"The job specification emphasizes {missing_skill}. How much hands-on exposure do you have with {missing_skill}, and how have you bridged similar gaps previously?",
                "rationale": f"Explicitly evaluates the identified skill gap ({missing_skill}) to determine learnability and ramp-up time.",
                "expected_answer": "Honest assessment of current proficiency, explanation of adjacent technologies (e.g. analogous tooling), and concrete examples of rapid skill acquisition.",
                "rubric_levels": {
                    "1": "Defensive or attempts to exaggerate familiarity with unverified tooling.",
                    "3": "Transparent about experience gap; demonstrates strong conceptual understanding of adjacent technologies.",
                    "5": "Demonstrates rapid self-guided mastery with working prototypes or analogous production implementations."
                },
                "follow_up_probes": [
                    f"How would you approach a critical task requiring {missing_skill} in your first two weeks?",
                    "What documentation and debugging resources do you rely on when learning new infrastructure?"
                ]
            },
            {
                "id": "q5",
                "category": "behavioral",
                "question": "Describe a production incident or severe bug you introduced or resolved. How did you triage, mitigate, and conduct the post-mortem?",
                "rationale": "Evaluates ownership, resilience under pressure, and systemic learning.",
                "expected_answer": "Candidate should emphasize immediate mitigation (rollback/hotfix), root-cause analysis without blame, and systemic preventive measures.",
                "rubric_levels": {
                    "1": "Blames external factors; does not demonstrate structured root-cause analysis.",
                    "3": "Structured triage story with clear technical resolution and lessons learned.",
                    "5": "Exemplary blameless post-mortem culture; implemented automated guards, monitoring alerts, and regression tests."
                },
                "follow_up_probes": [
                    "What metrics or alerting signals first notified the team of the issue?",
                    "How did you communicate system status to non-technical stakeholders during the incident?"
                ]
            }
        ]

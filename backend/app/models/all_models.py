import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="recruiter", nullable=False)  # super_admin, recruiter, hiring_manager
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    campaigns = relationship("Campaign", back_populates="user")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("MatchingAnalysis", back_populates="user")
    shortlists = relationship("Shortlist", back_populates="user")
    notes = relationship("RecruiterNote", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Campaign(Base):
    """
    Recruitment Campaign entity grouping multiple job openings, candidate pools,
    target headcount, and overall hiring velocity.
    """
    __tablename__ = "campaigns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    department = Column(String(100), default="Engineering", index=True)
    description = Column(Text, nullable=True)
    target_hires = Column(Integer, default=1)
    status = Column(String(50), default="active", index=True)  # active, draft, completed, paused, archived
    target_date = Column(String(50), nullable=True)
    settings = Column(JSON, nullable=True)  # default weights, screening strictness
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    jobs = relationship("Job", back_populates="campaign")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    location = Column(String(255), default="Remote")
    employment_type = Column(String(100), default="Full-time")
    min_experience = Column(Float, default=0.0)
    education_req = Column(String(255), default="Bachelor's Degree")
    description = Column(Text, nullable=False)
    extracted_requirements = Column(JSON, nullable=True)
    scoring_weights = Column(JSON, nullable=True)  # Custom weights: required_skills, projects, experience, preferred_skills, education
    criteria_approved = Column(Boolean, default=False)  # Recruiter review & approval checkpoint
    criteria_approved_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active", index=True)  # active, closed, draft
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="jobs")
    campaign = relationship("Campaign", back_populates="jobs")
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
    analyses = relationship("MatchingAnalysis", back_populates="job", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="job", cascade="all, delete-orphan")
    evaluation_runs = relationship("EvaluationRun", back_populates="job", cascade="all, delete-orphan")
    interview_kits = relationship("InterviewKit", back_populates="job", cascade="all, delete-orphan")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), default="mandatory")  # mandatory, preferred
    skill_type = Column(String(50), default="technical")  # technical, soft, tool, language, framework
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=utc_now)

    job = relationship("Job", back_populates="requirements")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    education = Column(JSON, nullable=True)
    total_experience_years = Column(Float, default=0.0)
    projects = Column(JSON, nullable=True)  # Structured project portfolio with tech stack & achievements
    certifications = Column(JSON, nullable=True)  # Verified certifications
    extracted_profile = Column(JSON, nullable=True)
    status = Column(String(50), default="new", index=True)  # new, analyzed, shortlisted, under_review, interview, rejected, hired
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    resume = relationship("Resume", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    analyses = relationship("MatchingAnalysis", back_populates="candidate", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="candidate", cascade="all, delete-orphan")
    notes = relationship("RecruiterNote", back_populates="candidate", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceReference", back_populates="candidate", cascade="all, delete-orphan")
    interview_kits = relationship("InterviewKit", back_populates="candidate", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    proficiency_level = Column(String(50), default="intermediate")
    source = Column(String(50), default="extracted")  # extracted, manual, verified
    evidence_type = Column(String(50), default="explicit")  # explicit, project, professional, inferred, not_found
    created_at = Column(DateTime, default=utc_now)

    candidate = relationship("Candidate", back_populates="skills")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for idempotent bulk upload
    raw_text = Column(Text, nullable=True)
    page_texts = Column(JSON, nullable=True)  # Text mapped per page: {"1": "...", "2": "..."}
    processing_status = Column(String(50), default="uploaded", index=True)  # uploaded, queued, parsing, evaluated, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    candidate = relationship("Candidate", back_populates="resume")
    evidence_items = relationship("EvidenceReference", back_populates="resume", cascade="all, delete-orphan")


class EvaluationRun(Base):
    """
    Versioned record of a matching evaluation run across a campaign or job.
    Enables recruiters to track historical evaluations, re-evaluate with updated
    criteria, and conduct What-If comparisons.
    """
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    run_name = Column(String(255), nullable=False)
    weights_snapshot = Column(JSON, nullable=False)
    criteria_snapshot = Column(JSON, nullable=True)
    candidate_count = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    job = relationship("Job", back_populates="evaluation_runs")
    analyses = relationship("MatchingAnalysis", back_populates="evaluation_run")


class MatchingAnalysis(Base):
    __tablename__ = "matching_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    evaluation_run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 0-100 Transparent Scoring components
    overall_score = Column(Float, nullable=False, default=0.0, index=True)
    technical_score = Column(Float, nullable=False, default=0.0)   # Required skills component
    projects_score = Column(Float, nullable=False, default=0.0)    # Relevant projects component
    experience_score = Column(Float, nullable=False, default=0.0)  # Professional tenure component
    preferred_score = Column(Float, nullable=False, default=0.0)   # Preferred/bonus skills component
    education_score = Column(Float, nullable=False, default=0.0)   # Education & certifications component
    semantic_score = Column(Float, nullable=False, default=0.0)    # Dense semantic cosine alignment
    
    weights_used = Column(JSON, nullable=True)  # Snapshot of weights applied
    confidence_score = Column(Float, default=0.90)  # AI extraction confidence (0.0 to 1.0)
    uncertainty_notes = Column(Text, nullable=True)  # Notes on unverified claims or sparse data
    
    explanation = Column(JSON, nullable=True)
    strengths = Column(JSON, default=list)
    skill_gaps = Column(JSON, default=list)
    matched_skills = Column(JSON, default=list)  # [{skill, type, evidence, confidence, source_page}]
    missing_skills = Column(JSON, default=list)  # List of strings
    related_skills = Column(JSON, default=list)  # List of strings
    
    created_at = Column(DateTime, default=utc_now, index=True)

    job = relationship("Job", back_populates="analyses")
    candidate = relationship("Candidate", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
    evaluation_run = relationship("EvaluationRun", back_populates="analyses")
    score_breakdowns = relationship("ScoreBreakdown", back_populates="analysis", cascade="all, delete-orphan")


class ScoreBreakdown(Base):
    __tablename__ = "score_breakdowns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("matching_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    component = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    weight_percentage = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    analysis = relationship("MatchingAnalysis", back_populates="score_breakdowns")


class EvidenceReference(Base):
    """
    Direct document evidence link connecting an evaluated criterion to an exact
    text quote, page number, and evidence strength classification in the original resume.
    """
    __tablename__ = "evidence_references"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    
    criterion = Column(String(255), nullable=False, index=True)
    criterion_type = Column(String(50), default="skill")  # skill, project, experience, education
    snippet = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    character_offset = Column(Integer, nullable=True)
    confidence = Column(Float, default=1.0)
    evidence_classification = Column(String(50), default="explicit")  # explicit, project, professional, inferred, not_found, unverified
    created_at = Column(DateTime, default=utc_now)

    candidate = relationship("Candidate", back_populates="evidence_items")
    resume = relationship("Resume", back_populates="evidence_items")


class InterviewKit(Base):
    """
    Personalized interview kit generated for a candidate against a job description,
    with structured technical, coding, project, and claim-verification rubrics.
    """
    __tablename__ = "interview_kits"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    questions = Column(JSON, nullable=False)  # List of {id, category, question, rationale, expected_answer, rubric_levels, follow_ups}
    rubric_guidelines = Column(JSON, nullable=True)
    evaluation_notes = Column(Text, nullable=True)
    status = Column(String(50), default="draft")  # draft, ready, completed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    candidate = relationship("Candidate", back_populates="interview_kits")
    job = relationship("Job", back_populates="interview_kits")


class Shortlist(Base):
    __tablename__ = "shortlists"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="shortlisted", index=True)  # shortlisted, interview, hired, rejected
    comments = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    job = relationship("Job", back_populates="shortlists")
    candidate = relationship("Candidate", back_populates="shortlists")
    user = relationship("User", back_populates="shortlists")


class RecruiterNote(Base):
    __tablename__ = "recruiter_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    candidate = relationship("Candidate", back_populates="notes")
    user = relationship("User", back_populates="notes")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String(50), default="info")  # success, info, warning, error
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    user = relationship("User", back_populates="notifications")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., "UPLOAD_RESUMES", "MATCH_JOB", "SHORTLIST"
    entity_type = Column(String(50), nullable=False)  # "job", "candidate", "resume", "analysis", "campaign"
    entity_id = Column(String(36), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)


class AgentExecution(Base):
    """
    Real agent observability record: tracks every agent invocation, execution latency,
    token consumption, model used, and outcome status without simulated metrics.
    """
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_name = Column(String(100), nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    target_entity_type = Column(String(50), nullable=True)  # "job", "candidate", "batch"
    target_entity_id = Column(String(36), nullable=True)
    status = Column(String(50), default="running", index=True)  # running, completed, failed, fallback
    
    duration_ms = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(100), nullable=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

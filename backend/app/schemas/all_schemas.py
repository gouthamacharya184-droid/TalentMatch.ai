from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # Resilient fallback if email-validator is not present

T = TypeVar("T")


# ── Generic Paginated Response ───────────────────────────
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
    model_config = ConfigDict(from_attributes=True)


# ── Auth & Users ──────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "recruiter"


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: str | None = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str | None = "recruiter"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


# ── Job Requirements & Jobs ───────────────────────────────
class JobRequirementBase(BaseModel):
    skill_name: str
    category: str = "mandatory"  # mandatory, preferred
    skill_type: str = "technical"  # technical, soft, tool, language, framework


class JobRequirementCreate(JobRequirementBase):
    pass


class JobRequirementResponse(JobRequirementBase):
    id: str
    job_id: str
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    title: str
    company: str
    location: str = "Remote"
    employment_type: str = "Full-time"
    min_experience: float = 0.0
    education_req: str = "Bachelor's Degree"
    description: str


class JobCreate(JobBase):
    requirements: list[JobRequirementCreate] | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    min_experience: float | None = None
    education_req: str | None = None
    description: str | None = None
    status: str | None = None
    requirements: list[JobRequirementCreate] | None = None


class JobResponse(JobBase):
    id: str
    user_id: str | None = None
    campaign_id: str | None = None
    status: str
    extracted_requirements: dict[str, Any] | None = None
    scoring_weights: dict[str, Any] | None = None
    criteria_approved: bool = False
    criteria_approved_at: datetime | None = None
    requirements: list[JobRequirementResponse] = []
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ── Candidate & Skills ────────────────────────────────────
class CandidateSkillBase(BaseModel):
    skill_name: str
    proficiency_level: str = "intermediate"
    source: str = "extracted"


class CandidateSkillResponse(CandidateSkillBase):
    id: str
    candidate_id: str
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    id: str
    candidate_id: str | None = None
    candidate_name: str | None = None
    original_filename: str
    stored_filename: str | None = None
    filename: str | None = None
    file_type: str
    file_size: int | None = 0
    raw_text: str | None = None
    processing_status: str
    status: str | None = None
    message: str | None = None
    error_message: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        res = super().model_validate(obj, *args, **kwargs)
        if res.filename is None:
            res.filename = res.original_filename
        if res.status is None:
            res.status = res.processing_status
        if res.candidate_name is None:
            cand = getattr(obj, "candidate", None)
            if cand and getattr(cand, "name", None):
                res.candidate_name = cand.name
        if res.message is None:
            res.message = res.error_message or (
                "Resume processed successfully" if res.processing_status == "completed" else "Processing failed"
            )
        return res


class CandidateBase(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    total_experience_years: float = 0.0


class CandidateCreate(CandidateBase):
    education: Any | None = None
    extracted_profile: dict[str, Any] | None = None
    skills: list[str] | None = None
    status: str | None = "new"


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    total_experience_years: float | None = None
    education: Any | None = None
    status: str | None = None


class CandidateResponse(CandidateBase):
    id: str
    user_id: str | None = None
    education: Any | None = None
    extracted_profile: dict[str, Any] | None = None
    status: str
    skills: list[CandidateSkillResponse] = []
    resume: ResumeResponse | None = None
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ── Matching Analysis ─────────────────────────────────────
class MatchingAnalysisResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    user_id: str | None = None
    overall_score: float
    technical_score: float
    semantic_score: float
    experience_score: float
    education_score: float
    explanation: dict[str, Any] | None = None
    strengths: list[str] = []
    skill_gaps: list[str] = []
    matched_skills: list[dict[str, Any]] = []
    missing_skills: list[str] = []
    related_skills: list[str] = []
    candidate: CandidateResponse | None = None
    job: JobResponse | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MatchRequest(BaseModel):
    job_id: str
    candidate_ids: list[str] | None = None
    weights: dict[str, float] | None = None


# ── Shortlist & Notes ─────────────────────────────────────
class ShortlistCreate(BaseModel):
    job_id: str
    candidate_id: str
    comments: str | None = ""


class ShortlistUpdateStatus(BaseModel):
    status: str


class ShortlistResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    user_id: str | None = None
    status: str
    comments: str | None = ""
    candidate: CandidateResponse | None = None
    analysis: MatchingAnalysisResponse | None = None
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class RecruiterNoteCreate(BaseModel):
    candidate_id: str
    job_id: str | None = None
    content: str


class RecruiterNoteResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str | None = None
    user_id: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ── Comparison ────────────────────────────────────────────
class CompareRequest(BaseModel):
    job_id: str
    candidate_ids: list[str]


class CandidateComparisonItem(BaseModel):
    candidate: CandidateResponse
    analysis: MatchingAnalysisResponse
    model_config = ConfigDict(from_attributes=True)


class SkillOverlapItem(BaseModel):
    skill: str
    candidates: dict[str, bool]


class ComparisonResponse(BaseModel):
    job: JobResponse
    candidates: list[CandidateComparisonItem]
    skill_overlap: list[SkillOverlapItem]
    model_config = ConfigDict(from_attributes=True)


# ── Notifications & Activity ──────────────────────────────
class NotificationResponse(BaseModel):
    id: str
    user_id: str | None = None
    type: str
    title: str
    message: str
    data: dict[str, Any] | None = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ActivityLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Dashboard & Analytics ─────────────────────────────────
class DashboardStatsResponse(BaseModel):
    total_jobs: int
    total_resumes: int
    total_candidates: int
    avg_matching_score: float
    total_shortlisted: int
    under_review: int
    recent_jobs: list[JobResponse] = []
    top_candidates: list[MatchingAnalysisResponse] = []
    score_distribution: dict[str, int] = {}
    skills_availability: dict[str, int] = {}
    recent_activity: list[ActivityLogResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ── Chatbot ───────────────────────────────────────────────
class ChatbotMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None
    job_id: str | None = None
    candidate_id: str | None = None
    page_context: str | None = None


class ChatbotMessageResponse(BaseModel):
    assistant_message: str
    message: str | None = None
    response: str | None = None
    conversation_id: str
    relevant_data: dict[str, Any] | None = None
    suggestions: list[str] | None = None
    mode: str = "llm"  # "llm" or "fallback"

    def model_post_init(self, __context: Any) -> None:
        if not self.message:
            self.message = self.assistant_message
        if not self.response:
            self.response = self.assistant_message


class ChatbotWelcomeResponse(BaseModel):
    welcome_message: str
    timestamp: str
    mode: str = "dynamic"
    stats: dict[str, Any] | None = None


# ── Enterprise Campaigns ─────────────────────────────────
class CampaignBase(BaseModel):
    name: str
    department: str = "Engineering"
    description: str | None = None
    target_hires: int = 1
    status: str = "active"
    target_date: str | None = None
    settings: dict[str, Any] | None = None


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    description: str | None = None
    target_hires: int | None = None
    status: str | None = None
    target_date: str | None = None
    settings: dict[str, Any] | None = None


class CampaignResponse(CampaignBase):
    id: str
    user_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    jobs: list[JobResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ── Scoring Weights & What-If Simulation ─────────────────
class ScoringWeights(BaseModel):
    required_skills: float = Field(35.0, ge=0.0, le=100.0)
    projects: float = Field(25.0, ge=0.0, le=100.0)
    experience: float = Field(15.0, ge=0.0, le=100.0)
    preferred_skills: float = Field(15.0, ge=0.0, le=100.0)
    education: float = Field(10.0, ge=0.0, le=100.0)


class CriteriaApprovalRequest(BaseModel):
    job_id: str
    approved: bool = True
    requirements: list[JobRequirementCreate] | None = None
    scoring_weights: ScoringWeights | None = None


class WhatIfSimulationRequest(BaseModel):
    job_id: str
    weights: ScoringWeights | None = None
    custom_weights: dict[str, float] | None = None
    modified_requirements: list[JobRequirementCreate] | None = None
    min_experience_override: float | None = None


class WhatIfCandidateDelta(BaseModel):
    candidate_id: str
    name: str
    candidate_name: str | None = None
    previous_score: float
    simulated_score: float
    score_delta: float
    previous_rank: int
    simulated_rank: int
    rank_delta: int
    impact_summary: str

    @model_validator(mode="before")
    @classmethod
    def populate_candidate_name(cls, data: Any):
        if isinstance(data, dict):
            if "candidate_name" not in data and "name" in data:
                data["candidate_name"] = data["name"]
            elif "name" not in data and "candidate_name" in data:
                data["name"] = data["candidate_name"]
        return data


class WhatIfSimulationResponse(BaseModel):
    job_id: str
    total_candidates_evaluated: int
    total_candidates: int | None = None
    average_score_before: float
    average_score_after: float
    significant_movers_count: int
    deltas: list[WhatIfCandidateDelta]
    rankings: list[WhatIfCandidateDelta] | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any):
        if isinstance(data, dict):
            if "total_candidates" not in data and "total_candidates_evaluated" in data:
                data["total_candidates"] = data["total_candidates_evaluated"]
            elif "total_candidates_evaluated" not in data and "total_candidates" in data:
                data["total_candidates_evaluated"] = data["total_candidates"]
            if "rankings" not in data and "deltas" in data:
                data["rankings"] = data["deltas"]
            elif "deltas" not in data and "rankings" in data:
                data["deltas"] = data["rankings"]
        return data


# ── Evidence References ──────────────────────────────────
class EvidenceReferenceResponse(BaseModel):
    id: str
    candidate_id: str
    resume_id: str | None = None
    job_id: str | None = None
    criterion: str
    criterion_type: str
    snippet: str
    page_number: int
    confidence: float
    evidence_classification: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Interview Intelligence Kits ──────────────────────────
class InterviewQuestionItem(BaseModel):
    id: str
    category: str  # technical, project, coding, behavioral, claim_verification
    question: str
    rationale: str
    expected_answer: str
    rubric_levels: dict[str, str] = {}  # "1": "poor", "3": "acceptable", "5": "exceptional"
    follow_up_probes: list[str] = []


class InterviewKitResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    user_id: str | None = None
    questions: list[InterviewQuestionItem] = []
    rubric_guidelines: dict[str, Any] | None = None
    evaluation_notes: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    candidate_name: str | None = None
    job_title: str | None = None
    model_config = ConfigDict(from_attributes=True)


class InterviewKitGenerateRequest(BaseModel):
    candidate_id: str
    job_id: str
    force_regenerate: bool = False


# ── Agent Observability ──────────────────────────────────
class AgentExecutionResponse(BaseModel):
    id: str
    agent_name: str
    task_name: str
    target_entity_type: str | None = None
    target_entity_id: str | None = None
    status: str
    duration_ms: int
    tokens_used: int
    model_used: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    error_message: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentActivityStats(BaseModel):
    total_executions: int
    active_agents: int
    success_rate_percent: float
    avg_latency_ms: float
    total_tokens_consumed: int
    recent_executions: list[AgentExecutionResponse] = []

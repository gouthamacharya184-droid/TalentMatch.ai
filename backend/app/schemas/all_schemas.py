from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

try:
    import email_validator
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # Resilient fallback if email-validator is not present

T = TypeVar("T")


# ── Generic Paginated Response ───────────────────────────
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
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
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "recruiter"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
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
    created_at: Optional[datetime] = None
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
    requirements: Optional[List[JobRequirementCreate]] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    min_experience: Optional[float] = None
    education_req: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    requirements: Optional[List[JobRequirementCreate]] = None


class JobResponse(JobBase):
    id: str
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    status: str
    extracted_requirements: Optional[Dict[str, Any]] = None
    scoring_weights: Optional[Dict[str, Any]] = None
    criteria_approved: bool = False
    criteria_approved_at: Optional[datetime] = None
    requirements: List[JobRequirementResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Candidate & Skills ────────────────────────────────────
class CandidateSkillBase(BaseModel):
    skill_name: str
    proficiency_level: str = "intermediate"
    source: str = "extracted"


class CandidateSkillResponse(CandidateSkillBase):
    id: str
    candidate_id: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    id: str
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    original_filename: str
    stored_filename: Optional[str] = None
    filename: Optional[str] = None
    file_type: str
    file_size: Optional[int] = 0
    raw_text: Optional[str] = None
    processing_status: str
    status: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
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
            res.message = res.error_message or ("Resume processed successfully" if res.processing_status == "completed" else "Processing failed")
        return res


class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    total_experience_years: float = 0.0


class CandidateCreate(CandidateBase):
    education: Optional[Any] = None
    extracted_profile: Optional[Dict[str, Any]] = None
    skills: Optional[List[str]] = None
    status: Optional[str] = "new"


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    total_experience_years: Optional[float] = None
    education: Optional[Any] = None
    status: Optional[str] = None


class CandidateResponse(CandidateBase):
    id: str
    user_id: Optional[str] = None
    education: Optional[Any] = None
    extracted_profile: Optional[Dict[str, Any]] = None
    status: str
    skills: List[CandidateSkillResponse] = []
    resume: Optional[ResumeResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Matching Analysis ─────────────────────────────────────
class MatchingAnalysisResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    user_id: Optional[str] = None
    overall_score: float
    technical_score: float
    semantic_score: float
    experience_score: float
    education_score: float
    explanation: Optional[Dict[str, Any]] = None
    strengths: List[str] = []
    skill_gaps: List[str] = []
    matched_skills: List[Dict[str, Any]] = []
    missing_skills: List[str] = []
    related_skills: List[str] = []
    candidate: Optional[CandidateResponse] = None
    job: Optional[JobResponse] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MatchRequest(BaseModel):
    job_id: str
    candidate_ids: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None


# ── Shortlist & Notes ─────────────────────────────────────
class ShortlistCreate(BaseModel):
    job_id: str
    candidate_id: str
    comments: Optional[str] = ""


class ShortlistUpdateStatus(BaseModel):
    status: str


class ShortlistResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    user_id: Optional[str] = None
    status: str
    comments: Optional[str] = ""
    candidate: Optional[CandidateResponse] = None
    analysis: Optional[MatchingAnalysisResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class RecruiterNoteCreate(BaseModel):
    candidate_id: str
    job_id: Optional[str] = None
    content: str


class RecruiterNoteResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Comparison ────────────────────────────────────────────
class CompareRequest(BaseModel):
    job_id: str
    candidate_ids: List[str]


class CandidateComparisonItem(BaseModel):
    candidate: CandidateResponse
    analysis: MatchingAnalysisResponse
    model_config = ConfigDict(from_attributes=True)


class SkillOverlapItem(BaseModel):
    skill: str
    candidates: Dict[str, bool]


class ComparisonResponse(BaseModel):
    job: JobResponse
    candidates: List[CandidateComparisonItem]
    skill_overlap: List[SkillOverlapItem]
    model_config = ConfigDict(from_attributes=True)


# ── Notifications & Activity ──────────────────────────────
class NotificationResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ActivityLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None
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
    recent_jobs: List[JobResponse] = []
    top_candidates: List[MatchingAnalysisResponse] = []
    score_distribution: Dict[str, int] = {}
    skills_availability: Dict[str, int] = {}
    recent_activity: List[ActivityLogResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ── Chatbot ───────────────────────────────────────────────
class ChatbotMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    page_context: Optional[str] = None


class ChatbotMessageResponse(BaseModel):
    assistant_message: str
    message: Optional[str] = None
    response: Optional[str] = None
    conversation_id: str
    relevant_data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
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
    stats: Optional[Dict[str, Any]] = None


# ── Enterprise Campaigns ─────────────────────────────────
class CampaignBase(BaseModel):
    name: str
    department: str = "Engineering"
    description: Optional[str] = None
    target_hires: int = 1
    status: str = "active"
    target_date: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    target_hires: Optional[int] = None
    status: Optional[str] = None
    target_date: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class CampaignResponse(CampaignBase):
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    jobs: List[JobResponse] = []
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
    requirements: Optional[List[JobRequirementCreate]] = None
    scoring_weights: Optional[ScoringWeights] = None


class WhatIfSimulationRequest(BaseModel):
    job_id: str
    weights: Optional[ScoringWeights] = None
    modified_requirements: Optional[List[JobRequirementCreate]] = None
    min_experience_override: Optional[float] = None


class WhatIfCandidateDelta(BaseModel):
    candidate_id: str
    name: str
    previous_score: float
    simulated_score: float
    score_delta: float
    previous_rank: int
    simulated_rank: int
    rank_delta: int
    impact_summary: str


class WhatIfSimulationResponse(BaseModel):
    job_id: str
    total_candidates_evaluated: int
    average_score_before: float
    average_score_after: float
    significant_movers_count: int
    deltas: List[WhatIfCandidateDelta]


# ── Evidence References ──────────────────────────────────
class EvidenceReferenceResponse(BaseModel):
    id: str
    candidate_id: str
    resume_id: Optional[str] = None
    job_id: Optional[str] = None
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
    rubric_levels: Dict[str, str] = {}  # "1": "poor", "3": "acceptable", "5": "exceptional"
    follow_up_probes: List[str] = []


class InterviewKitResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    user_id: Optional[str] = None
    questions: List[InterviewQuestionItem] = []
    rubric_guidelines: Optional[Dict[str, Any]] = None
    evaluation_notes: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
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
    target_entity_type: Optional[str] = None
    target_entity_id: Optional[str] = None
    status: str
    duration_ms: int
    tokens_used: int
    model_used: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentActivityStats(BaseModel):
    total_executions: int
    active_agents: int
    success_rate_percent: float
    avg_latency_ms: float
    total_tokens_consumed: int
    recent_executions: List[AgentExecutionResponse] = []



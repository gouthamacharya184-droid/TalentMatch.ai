// ============================================================
// TalentMatch AI — TypeScript Interfaces
// ============================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'super_admin' | 'recruiter' | 'hiring_manager';
  is_active?: boolean;
  last_login?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ScoringWeights {
  required_skills?: number;
  relevant_projects?: number;
  professional_experience?: number;
  preferred_skills?: number;
  education_certifications?: number;
  [key: string]: number | undefined;
}

export interface Job {
  id: string;
  user_id?: string;
  campaign_id?: string | null;
  title: string;
  company: string;
  location: string;
  employment_type: string;
  min_experience: number;
  education_req: string;
  description: string;
  extracted_requirements: Record<string, unknown> | null;
  scoring_weights?: ScoringWeights | null;
  criteria_approved?: boolean;
  criteria_approved_at?: string | null;
  status: 'active' | 'closed' | 'draft';
  created_at: string;
  updated_at?: string;
  requirements?: JobRequirement[];
}

export interface JobRequirement {
  id: string;
  job_id: string;
  skill_name: string;
  category: 'mandatory' | 'preferred';
  skill_type: 'technical' | 'soft' | 'tool' | 'language' | 'framework';
  created_at?: string;
}

export interface Candidate {
  id: string;
  user_id?: string;
  name: string;
  email: string;
  phone: string;
  location: string;
  education: Record<string, unknown> | null;
  total_experience_years: number;
  projects?: Array<Record<string, unknown>> | null;
  certifications?: Array<Record<string, unknown>> | null;
  extracted_profile: Record<string, unknown> | null;
  status: 'new' | 'analyzed' | 'shortlisted' | 'under_review' | 'interview' | 'rejected' | 'hired';
  skills: CandidateSkill[];
  resume?: Resume;
  created_at: string;
  updated_at?: string;
}

export interface CandidateSkill {
  id: string;
  candidate_id?: string;
  skill_name: string;
  proficiency_level: string;
  source: 'extracted' | 'manual';
  created_at?: string;
}

export interface Resume {
  id: string;
  candidate_id?: string | null;
  original_filename: string;
  filename?: string;
  stored_filename?: string;
  file_path?: string;
  file_type: string;
  file_size?: number;
  raw_text?: string;
  processing_status: 'uploaded' | 'queued' | 'processing' | 'completed' | 'failed';
  status?: string;
  message?: string;
  error_message?: string;
  created_at: string;
}

export interface MatchingAnalysis {
  id: string;
  job_id: string;
  candidate_id: string;
  user_id?: string;
  evaluation_run_id?: string | null;
  overall_score: number;
  technical_score: number;
  projects_score?: number;
  semantic_score: number;
  experience_score: number;
  preferred_score?: number;
  education_score: number;
  confidence_score?: number;
  uncertainty_notes?: string | null;
  weights_used?: ScoringWeights | null;
  explanation: Record<string, unknown> | null;
  strengths: string[];
  skill_gaps: string[];
  matched_skills: SkillMatch[];
  missing_skills: string[];
  related_skills: string[];
  candidate?: Candidate;
  job?: Job;
  created_at: string;
}

export interface SkillMatch {
  skill: string;
  type: 'exact' | 'related' | 'partial';
  evidence: string;
  confidence: number;
}

export interface ScoreBreakdown {
  id: string;
  analysis_id: string;
  component: string;
  score: number;
  max_score: number;
  details: Record<string, unknown> | null;
  created_at?: string;
}

export interface Shortlist {
  id: string;
  job_id: string;
  candidate_id: string;
  user_id?: string;
  status: 'shortlisted' | 'interview' | 'hired' | 'rejected';
  comments: string;
  candidate?: Candidate;
  analysis?: MatchingAnalysis;
  created_at: string;
  updated_at?: string;
}

export interface RecruiterNote {
  id: string;
  candidate_id: string;
  job_id?: string;
  user_id?: string;
  content: string;
  created_at: string;
  updated_at?: string;
}

export interface Notification {
  id: string;
  user_id?: string;
  type: string;
  title: string;
  message: string;
  data?: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export interface ActivityLog {
  id: string;
  user_id?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface DashboardStats {
  total_jobs: number;
  total_resumes: number;
  total_candidates: number;
  avg_matching_score: number;
  total_shortlisted: number;
  under_review: number;
  recent_jobs: Job[];
  top_candidates: MatchingAnalysis[];
  score_distribution?: Record<string, number>;
  skills_availability?: Record<string, number>;
  recent_activity?: ActivityLog[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  role?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: User;
}

export interface ComparisonResult {
  job: Job;
  candidates: CandidateComparisonData[];
  skill_overlap: SkillOverlapEntry[];
}

export interface CandidateComparisonData {
  candidate: Candidate;
  analysis: MatchingAnalysis;
}

export interface SkillOverlapEntry {
  skill: string;
  candidates: Record<string, boolean>;
}

export interface ReportExport {
  job: Job;
  analyses: MatchingAnalysis[];
  generated_at: string;
}

export interface CandidateFilters {
  search?: string;
  status?: string;
  skills?: string[];
  min_experience?: number;
  max_experience?: number;
  skip?: number;
  limit?: number;
}

export interface MatchingFilters {
  min_score?: number;
  max_score?: number;
  skills?: string[];
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ── Chatbot ───────────────────────────────────────────────
export interface ChatbotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  mode?: 'llm' | 'fallback' | 'dynamic';
  relevant_data?: Record<string, unknown> | null;
  suggestions?: string[];
  error?: boolean;
}

export interface ChatbotResponse {
  assistant_message: string;
  conversation_id: string;
  relevant_data?: Record<string, unknown> | null;
  suggestions?: string[];
  mode: 'llm' | 'fallback';
}

export interface ChatbotWelcomeResponse {
  welcome_message: string;
  timestamp: string;
  mode: 'dynamic' | 'llm' | 'fallback';
  stats?: Record<string, unknown>;
}

// ── Agentic Recruitment Platform Types ───────────────────

export interface EvidenceReference {
  id: string;
  candidate_id: string;
  resume_id?: string;
  job_id?: string;
  claim_type: string;
  claim_text: string;
  source_document?: string;
  page_number?: number;
  exact_quote?: string;
  confidence_level?: string;
  verification_method?: string;
  created_at?: string;
}

export interface Campaign {
  id: string;
  title: string;
  description?: string;
  status: 'draft' | 'active' | 'paused' | 'closed' | string;
  target_headcount: number;
  hired_count: number;
  department?: string;
  owner_id?: string;
  created_at: string;
  updated_at?: string;
  jobs?: Job[];
}

export interface CampaignCreate {
  title: string;
  description?: string;
  status?: string;
  target_headcount?: number;
  department?: string;
}

export interface InterviewQuestionItem {
  question: string;
  category: 'technical' | 'project' | 'coding' | 'behavioral' | 'claim_verification' | string;
  purpose?: string;
  claim_to_verify?: string;
  expected_indicators?: string[];
  rubric?: Record<string, string>;
  follow_ups?: string[];
}

export interface InterviewKit {
  id: string;
  job_id: string;
  candidate_id: string;
  created_by?: string;
  kit_type?: string;
  questions: InterviewQuestionItem[];
  evaluation_rubric?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
  candidate?: Candidate;
  job?: Job;
}

export interface AgentExecution {
  id: string;
  agent_name: string;
  job_id?: string;
  candidate_id?: string;
  status: 'success' | 'failed' | 'timeout' | string;
  execution_time_ms: number;
  tokens_used: number;
  model_name: string;
  error_message?: string;
  metadata_json?: Record<string, unknown>;
  created_at: string;
}

export interface AgentActivityStats {
  total_executions: number;
  success_rate: number;
  avg_latency_ms: number;
  total_tokens: number;
  by_agent: Record<
    string,
    {
      executions: number;
      avg_latency_ms: number;
      success_rate: number;
      total_tokens: number;
    }
  >;
  recent_failures: AgentExecution[];
}

export interface WhatIfSimulationRequest {
  job_id: string;
  custom_weights: {
    required_skills?: number;
    relevant_projects?: number;
    professional_experience?: number;
    preferred_skills?: number;
    education_certifications?: number;
    [key: string]: number | undefined;
  };
}

export interface WhatIfCandidateDelta {
  candidate_id: string;
  candidate_name: string;
  previous_score: number;
  simulated_score: number;
  score_delta: number;
  previous_rank: number;
  simulated_rank: number;
  rank_delta: number;
  component_breakdown: Record<string, number>;
}

export interface WhatIfSimulationResponse {
  job_id: string;
  weights_used: Record<string, number>;
  total_candidates: number;
  rankings: WhatIfCandidateDelta[];
}



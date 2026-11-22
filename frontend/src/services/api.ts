import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Job,
  JobRequirement,
  Resume,
  Candidate,
  CandidateSkill,
  MatchingAnalysis,
  Shortlist,
  RecruiterNote,
  Notification,
  DashboardStats,
  PaginatedResponse,
  ComparisonResult,
  CandidateFilters,
  ReportExport,
  ChatbotResponse,
  ChatbotWelcomeResponse,
  Campaign,
  CampaignCreate,
  EvidenceReference,
  InterviewKit,
  AgentExecution,
  AgentActivityStats,
  WhatIfSimulationRequest,
  WhatIfSimulationResponse,
} from '../types';

// ── Axios instance ──────────────────────────────────────────
const rawBase = (import.meta.env.VITE_API_URL as string) || (import.meta.env.VITE_API_BASE_URL as string) || '/api';
const baseURL = rawBase.endsWith('/') ? rawBase.slice(0, -1) : rawBase;

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT and handle multipart/form-data
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // When sending FormData, remove Content-Type so browser sets boundary automatically
  if (config.data instanceof FormData && config.headers) {
    delete config.headers['Content-Type'];
  }
  return config;
});

// Response interceptor — handle 401 cleanly without abrupt window.location reload
api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.dispatchEvent(new CustomEvent('talentmatch:unauthorized'));
    }
    return Promise.reject(error);
  },
);

// ── Auth ─────────────────────────────────────────────────────
export const authApi = {
  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    api.post<AuthResponse>('/auth/register', data).then((r) => r.data),

  logout: () => api.post('/auth/logout').then((r) => r.data),

  refreshToken: () =>
    api.post<AuthResponse>('/auth/refresh').then((r) => r.data),

  getMe: () => api.get<User>('/auth/me').then((r) => r.data),

  updateProfile: (data: Partial<User> & { password?: string }) =>
    api.put<User>('/auth/profile', data).then((r) => r.data),
};

// ── Jobs ─────────────────────────────────────────────────────
export const jobsApi = {
  getJobs: (params?: { skip?: number; limit?: number; search?: string; status?: string }) =>
    api.get<PaginatedResponse<Job>>('/jobs', { params }).then((r) => r.data),

  getJob: (id: string) => api.get<Job>(`/jobs/${id}`).then((r) => r.data),

  createJob: (data: Partial<Job>) =>
    api.post<Job>('/jobs', data).then((r) => r.data),

  updateJob: (id: string, data: Partial<Job>) =>
    api.put<Job>(`/jobs/${id}`, data).then((r) => r.data),

  deleteJob: (id: string) => api.delete(`/jobs/${id}`).then((r) => r.data),

  extractRequirements: (id: string) =>
    api.post<JobRequirement[]>(`/jobs/${id}/extract-requirements`).then((r) => r.data),

  updateRequirements: (id: string, requirements: Partial<JobRequirement>[]) =>
    api.put<JobRequirement[]>(`/jobs/${id}/requirements`, requirements).then((r) => r.data),

  uploadJDDocument: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api
      .post<any>('/jobs/upload-jd', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data);
  },

  approveCriteria: (id: string, customWeights?: Record<string, number>) =>
    api.post<Job>(`/jobs/${id}/approve-criteria`, { custom_weights: customWeights }).then((r) => r.data),
};

// ── Resumes ──────────────────────────────────────────────────
export const resumesApi = {
  uploadResumes: (files: File[], onProgress?: (percent: number) => void) => {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    return api
      .post<Resume[]>('/resumes/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      })
      .then((r) => r.data);
  },

  uploadSingleResume: (file: File, onProgress?: (percent: number) => void) => {
    const form = new FormData();
    form.append('files', file);
    return api
      .post<Resume[]>('/resumes/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      })
      .then((r) => r.data[0]);
  },

  getResumeStatus: (id: string) =>
    api.get<Resume>(`/resumes/${id}/status`).then((r) => r.data),

  getResume: (id: string) =>
    api.get<Resume>(`/resumes/${id}`).then((r) => r.data),

  getResumeViewUrl: (id: string) =>
    `${api.defaults.baseURL || '/api/v1'}/resumes/${id}/view`,

  downloadResume: (id: string) =>
    api.get(`/resumes/${id}/download`, { responseType: 'blob' }).then((r) => r.data),

  deleteResume: (id: string) =>
    api.delete(`/resumes/${id}`).then((r) => r.data),

  loadSampleBatch: () =>
    api.post<Resume[]>('/resumes/load-sample-batch').then((r) => r.data),

  getResumes: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get<PaginatedResponse<Resume>>('/resumes', { params }).then((r) => r.data),
};

// ── Candidates ───────────────────────────────────────────────
export const candidatesApi = {
  getCandidates: (filters?: CandidateFilters) =>
    api.get<PaginatedResponse<Candidate>>('/candidates', { params: filters }).then((r) => r.data),

  getCandidate: (id: string) =>
    api.get<Candidate>(`/candidates/${id}`).then((r) => r.data),

  updateCandidate: (id: string, data: Partial<Candidate>) =>
    api.put<Candidate>(`/candidates/${id}`, data).then((r) => r.data),

  deleteCandidate: (id: string) =>
    api.delete(`/candidates/${id}`).then((r) => r.data),

  getCandidateSkills: (id: string) =>
    api.get<CandidateSkill[]>(`/candidates/${id}/skills`).then((r) => r.data),

  getEvidence: (id: string, jobId?: string) =>
    api.get<EvidenceReference[]>(`/candidates/${id}/evidence`, { params: { job_id: jobId } }).then((r) => r.data),
};

// ── Matching ─────────────────────────────────────────────────
export interface RecommendedJob {
  job_id: string;
  title: string;
  company: string;
  location: string;
  min_experience: number;
  fit_score: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendation_reason: string;
}

export const matchingApi = {
  analyzeMatch: (jobId: string, candidateIds: string[], weights?: Record<string, number>) =>
    api
      .post<MatchingAnalysis[]>('/matching/analyze', { job_id: jobId, candidate_ids: candidateIds, weights })
      .then((r) => r.data),

  getResults: (jobId: string) =>
    api.get<MatchingAnalysis[]>(`/matching/results/${jobId}`).then((r) => r.data),

  getAnalysis: (id: string) =>
    api.get<MatchingAnalysis>(`/matching/analysis/${id}`).then((r) => r.data),

  getRankings: (jobId: string, params?: { sort_by?: string; sort_order?: string; min_score?: number }) =>
    api.get<MatchingAnalysis[]>(`/matching/rankings/${jobId}`, { params }).then((r) => r.data),

  simulateWhatIf: (data: WhatIfSimulationRequest) =>
    api.post<WhatIfSimulationResponse>('/matching/what-if', data).then((r) => r.data),

  getRecommendedJobs: (candidateId: string, excludeJobId?: string) =>
    api
      .get<RecommendedJob[]>(`/matching/candidate/${candidateId}/recommend-jobs`, {
        params: { exclude_job_id: excludeJobId },
      })
      .then((r) => r.data),
};

// ── Comparison ───────────────────────────────────────────────
export const comparisonApi = {
  compareCandidates: (jobId: string, candidateIds: string[]) =>
    api
      .post<ComparisonResult>('/comparison/compare', {
        job_id: jobId,
        candidate_ids: candidateIds,
      })
      .then((r) => r.data),
};

// ── Shortlist ────────────────────────────────────────────────
export const shortlistApi = {
  addToShortlist: (jobId: string, candidateId: string, comments?: string) =>
    api
      .post<Shortlist>('/shortlist', { job_id: jobId, candidate_id: candidateId, comments })
      .then((r) => r.data),

  removeFromShortlist: (id: string) =>
    api.delete(`/shortlist/${id}`).then((r) => r.data),

  getJobShortlist: (jobId: string) =>
    api.get<Shortlist[]>(`/shortlist/job/${jobId}`).then((r) => r.data),

  updateShortlistStatus: (id: string, status: string) =>
    api.put<Shortlist>(`/shortlist/${id}/status`, { status }).then((r) => r.data),

  addNote: (candidateId: string, jobId: string, content: string) =>
    api.post<RecruiterNote>('/shortlist/notes', { candidate_id: candidateId, job_id: jobId, content }).then((r) => r.data),

  getNotes: (candidateId: string, jobId?: string) =>
    api.get<RecruiterNote[]>(`/shortlist/notes/${candidateId}`, { params: { job_id: jobId } }).then((r) => r.data),
};

// ── Analytics ────────────────────────────────────────────────
export const analyticsApi = {
  getDashboard: () =>
    api.get<DashboardStats>('/analytics/dashboard').then((r) => r.data),

  getReports: (jobId: string) =>
    api.get<ReportExport>(`/analytics/reports/${jobId}`).then((r) => r.data),

  exportReport: (jobId: string, format: 'csv' | 'xlsx' | 'pdf') =>
    api
      .get(`/analytics/reports/${jobId}/export`, {
        params: { format },
        responseType: 'blob',
      })
      .then((r) => r.data),

  getHistory: (params?: { skip?: number; limit?: number }) =>
    api.get<PaginatedResponse<MatchingAnalysis>>('/analytics/history', { params }).then((r) => r.data),
};

// ── Notifications ────────────────────────────────────────────
export const notificationsApi = {
  getNotifications: (params?: { skip?: number; limit?: number }) =>
    api.get<PaginatedResponse<Notification>>('/notifications', { params }).then((r) => r.data),

  markRead: (id: string) =>
    api.put(`/notifications/${id}/read`).then((r) => r.data),

  markAllRead: () =>
    api.put('/notifications/read-all').then((r) => r.data),

  getUnreadCount: () =>
    api.get<{ count: number }>('/notifications/unread-count').then((r) => r.data),
};

// ── Chatbot ──────────────────────────────────────────────────
export const chatbotApi = {
  sendMessage: (data: {
    message: string;
    conversation_id?: string;
    job_id?: string;
    candidate_id?: string;
    page_context?: string;
  }) => api.post<ChatbotResponse>('/chatbot/chat', data).then((r) => r.data),

  clearConversation: (conversationId: string) =>
    api.post(`/chatbot/clear/${conversationId}`).then((r) => r.data),

  getSuggestions: () =>
    api.get<string[]>('/chatbot/suggestions').then((r) => r.data),

  getWelcomeMessage: (params?: { page_context?: string; job_id?: string; candidate_id?: string }) =>
    api.get<ChatbotWelcomeResponse>('/chatbot/welcome', { params }).then((r) => r.data),
};

// ── Campaigns ────────────────────────────────────────────────
// Backend uses `name` / `target_hires`; the UI uses `title` / `target_headcount`.
type CampaignApiRecord = {
  id: string;
  name?: string;
  title?: string;
  description?: string;
  status?: string;
  department?: string;
  target_hires?: number;
  target_headcount?: number;
  hired_count?: number;
  created_at: string;
  updated_at?: string;
  jobs?: Job[];
};

const toCampaign = (c: CampaignApiRecord): Campaign => ({
  ...c,
  title: c.title ?? c.name ?? '',
  status: c.status ?? 'active',
  target_headcount: c.target_headcount ?? c.target_hires ?? 1,
  hired_count: c.hired_count ?? 0,
});

const toCampaignPayload = ({ title, target_headcount, ...rest }: Partial<CampaignCreate>) => ({
  ...rest,
  ...(title !== undefined ? { name: title } : {}),
  ...(target_headcount !== undefined ? { target_hires: target_headcount } : {}),
});

export const campaignsApi = {
  getCampaigns: (params?: { status?: string }) =>
    api.get<{ items: CampaignApiRecord[] }>('/campaigns', { params })
      .then((r) => r.data.items.map(toCampaign)),

  getCampaign: (id: string) =>
    api.get<CampaignApiRecord>(`/campaigns/${id}`).then((r) => toCampaign(r.data)),

  createCampaign: (data: CampaignCreate) =>
    api.post<CampaignApiRecord>('/campaigns', toCampaignPayload(data)).then((r) => toCampaign(r.data)),

  updateCampaign: (id: string, data: Partial<CampaignCreate> & { status?: string; hired_count?: number }) =>
    api.put<CampaignApiRecord>(`/campaigns/${id}`, toCampaignPayload(data)).then((r) => toCampaign(r.data)),

  deleteCampaign: (id: string) =>
    api.delete(`/campaigns/${id}`).then((r) => r.data),

  linkJob: (campaignId: string, jobId: string) =>
    api.post<CampaignApiRecord>(`/campaigns/${campaignId}/jobs/${jobId}`).then((r) => toCampaign(r.data)),
};

// ── Interview Kits ───────────────────────────────────────────
export const interviewKitsApi = {
  generateKit: (jobId: string, candidateId: string) =>
    api
      .post<InterviewKit>('/interview-kits/generate', { job_id: jobId, candidate_id: candidateId })
      .then((r) => r.data),

  getKit: (id: string) =>
    api.get<InterviewKit>(`/interview-kits/${id}`).then((r) => r.data),

  getKitForCandidate: (candidateId: string, jobId?: string) =>
    api
      .get<InterviewKit>(`/interview-kits/candidate/${candidateId}`, { params: { job_id: jobId } })
      .then((r) => r.data),

  listKits: (params?: { job_id?: string; candidate_id?: string }) =>
    api.get<InterviewKit[]>('/interview-kits', { params }).then((r) => r.data),
};

// ── Agent Observability ──────────────────────────────────────
export const agentsApi = {
  getExecutions: (params?: { agent_name?: string; status?: string; limit?: number }) =>
    api.get<AgentExecution[]>('/agents/executions', { params }).then((r) => r.data),

  getStats: () =>
    api.get<AgentActivityStats>('/agents/stats').then((r) => r.data),
};

export default api;

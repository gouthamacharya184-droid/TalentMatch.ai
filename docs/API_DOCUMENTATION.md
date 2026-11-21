# TalentMatch.ai — Comprehensive REST API Specification

**Base URL:** `/api` (or `http://localhost:8000/api`)  
**Specification Version:** OpenAPI 3.1.0  
**Authentication Scheme:** Bearer Token (JWT in `Authorization: Bearer <token>` header)

---

## 1. Authentication Endpoints (`/api/auth`)

### `POST /api/auth/register`
Register a new recruiter or administrator.
- **Request Body:**
  ```json
  {
    "full_name": "Jane Recruiter",
    "email": "jane@company.com",
    "password": "SecurePassword123!",
    "role": "recruiter"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "usr_uuid",
      "email": "jane@company.com",
      "full_name": "Jane Recruiter",
      "role": "recruiter"
    }
  }
  ```

### `POST /api/auth/login`
Authenticate credentials and issue JWT.
- **Request Body:**
  ```json
  {
    "email": "jane@company.com",
    "password": "SecurePassword123!"
  }
  ```

### `GET /api/auth/me`
Retrieve profile of currently authenticated user.

---

## 2. Recruitment Campaigns (`/api/campaigns`)

### `GET /api/campaigns`
List all recruitment campaigns with optional status filtering.
- **Query Parameters:** `status` (optional: `draft`, `active`, `paused`, `closed`)

### `POST /api/campaigns`
Create a new recruitment campaign.
- **Request Body:**
  ```json
  {
    "title": "Q3 Engineering Growth",
    "description": "Strategic hiring drive for distributed backend team",
    "department": "Engineering",
    "target_headcount": 5,
    "status": "active"
  }
  ```

### `POST /api/campaigns/{campaign_id}/jobs/{job_id}`
Link an existing job opening to a recruitment campaign.

---

## 3. Job Descriptions & Criteria Staging (`/api/jobs`)

### `POST /api/jobs`
Create a job opening with AI requirements extraction.
- **Request Body:**
  ```json
  {
    "title": "Senior Staff Python Engineer",
    "company": "AVOM Consultants",
    "location": "Remote",
    "min_experience": 5.0,
    "education_req": "Bachelor's Degree",
    "description": "Full JD text..."
  }
  ```

### `POST /api/jobs/upload-jd`
Upload a PDF, DOCX, or TXT file to parse job description content automatically via `JobDescriptionAgent`.

### `POST /api/jobs/{id}/approve-criteria`
Human-in-the-loop checkpoint: Approve extracted criteria and configure custom scoring weights.
- **Request Body:**
  ```json
  {
    "custom_weights": {
      "required_skills": 35,
      "relevant_projects": 25,
      "professional_experience": 15,
      "preferred_skills": 15,
      "education_certifications": 10
    }
  }
  ```
- **Response (200 OK):** Job object with `criteria_approved: true` and timestamp.

---

## 4. Resume Ingestion & Processing (`/api/resumes`)

### `POST /api/resumes/upload`
Upload single or batch resume documents (`multipart/form-data`).
- **Form Data:** `files: UploadFile[]`
- **Supported Formats:** `.pdf`, `.docx`, `.doc`, `.txt` (up to 25 MB per file).
- **Features:** SHA-256 deduplication, multi-page segmentation, error isolation.

---

## 5. Candidate Intelligence & Evidence Retrieval (`/api/candidates`)

### `GET /api/candidates`
Paginated search and filter across candidates.
- **Query Parameters:** `search`, `status`, `min_experience`, `skip`, `limit`.

### `GET /api/candidates/{id}/evidence`
Retrieve 6-tier evidence citations linking candidate claims to source document text.
- **Query Parameters:** `job_id` (optional).
- **Response (200 OK):**
  ```json
  [
    {
      "id": "ev_uuid",
      "candidate_id": "cand_uuid",
      "claim_type": "technical_skill",
      "claim_text": "Python",
      "source_document": "Jane_Doe_Resume.pdf",
      "page_number": 1,
      "exact_quote": "Architected Python microservices handling 10k RPS",
      "confidence_level": "demonstrated_professionally"
    }
  ]
  ```

---

## 6. AI Matching & What-If Sensitivity (`/api/matching`)

### `POST /api/matching/analyze`
Trigger agentic evaluation between a job and candidate batch.
- **Request Body:**
  ```json
  {
    "job_id": "job_uuid",
    "candidate_ids": ["cand_uuid_1", "cand_uuid_2"]
  }
  ```

### `GET /api/matching/rankings/{job_id}`
Retrieve candidate rankings sorted by overall match score or specific component score.

### `POST /api/matching/what-if`
Execute interactive What-If sensitivity simulation with custom scoring weights.
- **Request Body:**
  ```json
  {
    "job_id": "job_uuid",
    "custom_weights": {
      "required_skills": 50,
      "relevant_projects": 30,
      "professional_experience": 10,
      "preferred_skills": 5,
      "education_certifications": 5
    }
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "job_id": "job_uuid",
    "total_candidates": 15,
    "weights_used": { "required_skills": 50, ... },
    "rankings": [
      {
        "candidate_id": "cand_uuid",
        "candidate_name": "Alex Smith",
        "previous_score": 78.4,
        "simulated_score": 84.1,
        "score_delta": 5.7,
        "previous_rank": 4,
        "simulated_rank": 1,
        "rank_delta": 3,
        "component_breakdown": { "required_skills": 42.0, ... }
      }
    ]
  }
  ```

---

## 7. Interview Intelligence (`/api/interview-kits`)

### `POST /api/interview-kits/generate`
Formulate tailored, evidence-grounded interview kit via `InterviewIntelligenceAgent`.
- **Request Body:**
  ```json
  {
    "job_id": "job_uuid",
    "candidate_id": "cand_uuid"
  }
  ```

### `GET /api/interview-kits/candidate/{candidate_id}`
Retrieve stored interview kit for a specific candidate.

---

## 8. Agent Observability & Telemetry (`/api/agents`)

### `GET /api/agents/executions`
Stream execution audit logs across all 8 agents.
- **Query Parameters:** `agent_name`, `status`, `limit`.

### `GET /api/agents/stats`
Retrieve aggregated latency, reliability, and token consumption metrics.
- **Response (200 OK):**
  ```json
  {
    "total_executions": 320,
    "success_rate": 100.0,
    "avg_latency_ms": 14.8,
    "total_tokens": 128400,
    "by_agent": {
      "JobDescriptionAgent": { "executions": 19, "avg_latency_ms": 12.1, "success_rate": 100.0, "total_tokens": 8500 },
      "CandidateMatchingAgent": { "executions": 140, "avg_latency_ms": 16.4, "success_rate": 100.0, "total_tokens": 42000 }
    }
  }
  ```

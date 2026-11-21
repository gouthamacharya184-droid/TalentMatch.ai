# API DOCUMENTATION — TALENTMATCH AI REST API

**Base URL:** `http://localhost:8000/api`  
**Interactive Swagger UI:** `http://localhost:8000/docs`  
**ReDoc UI:** `http://localhost:8000/redoc`  
**Authentication:** HTTP Bearer Header (`Authorization: Bearer <access_token>`)  
**Version:** 1.0.0 Production  

---

## 1. Authentication & User Management

### 1.1 User Login
- **Endpoint:** `POST /api/auth/login`
- **Request Body:**
  ```json
  {
    "email": "recruiter@talentmatch.ai",
    "password": "Recruiter@123456"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "id": "user-uuid",
      "email": "recruiter@talentmatch.ai",
      "full_name": "Senior Tech Recruiter",
      "role": "recruiter"
    }
  }
  ```
- **Errors:** 401 Unauthorized (Invalid credentials), 422 Unprocessable Entity (Validation error).

### 1.2 User Registration
- **Endpoint:** `POST /api/auth/register`
- **Request Body:**
  ```json
  {
    "full_name": "Jane Doe",
    "email": "jane.doe@avomconsultants.com",
    "password": "SecurePassword123!",
    "role": "recruiter"
  }
  ```
- **Response (200 OK):** User object and JWT token.

### 1.3 Get Current User
- **Endpoint:** `GET /api/auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** User profile information.

### 1.4 Refresh Token
- **Endpoint:** `POST /api/auth/refresh`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Refreshed access token.

---

## 2. Job Description Management

### 2.1 List Jobs
- **Endpoint:** `GET /api/jobs`
- **Query Params:** `skip=0`, `limit=50`, `search=...`, `status=active`
- **Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "job-uuid",
        "title": "Lead AI/NLP Engineer",
        "company": "AVOM Consultants",
        "location": "Remote",
        "employment_type": "Full-time",
        "min_experience": 5.0,
        "education_req": "Master's Degree in Computer Science or related",
        "status": "active",
        "requirements": [
          {"skill_name": "Python", "category": "mandatory", "skill_type": "language"},
          {"skill_name": "PyTorch", "category": "mandatory", "skill_type": "framework"}
        ]
      }
    ],
    "total": 12,
    "skip": 0,
    "limit": 50
  }
  ```

### 2.2 Create Job
- **Endpoint:** `POST /api/jobs`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "title": "Senior Backend Engineer",
    "company": "AVOM Consultants",
    "description": "We are seeking a Senior Backend Engineer proficient in Python, FastAPI, PostgreSQL, Docker, and AWS.",
    "min_experience": 4.0,
    "education_req": "Bachelor's Degree",
    "location": "Remote",
    "employment_type": "Full-time"
  }
  ```

### 2.3 Upload Job Description Document
- **Endpoint:** `POST /api/jobs/upload-jd`
- **Form Data:** `file: <binary document (.pdf, .docx, .txt)>`
- **Response (200 OK):** Automatically parsed job attributes and extracted requirements.

### 2.4 Extract Requirements from Description
- **Endpoint:** `POST /api/jobs/{id}/extract-requirements`
- **Response (200 OK):** List of extracted mandatory and preferred skill requirements.

---

## 3. Bulk Resume Upload & Management

### 3.1 Bulk Upload Resumes
- **Endpoint:** `POST /api/resumes/upload`
- **Headers:** `Authorization: Bearer <token>` (Optional)
- **Form Data:** `files: <binary[]>` (1 to 50 files; PDF, DOCX, TXT)
- **Response (200 OK):**
  ```json
  [
    {
      "id": "resume-uuid",
      "candidate_id": "candidate-uuid",
      "original_filename": "Alex_Chen_Senior_FullStack.pdf",
      "stored_filename": "uuid.pdf",
      "file_type": "pdf",
      "file_size": 2711,
      "processing_status": "completed",
      "created_at": "2026-11-20T21:00:00Z"
    }
  ]
  ```

### 3.2 List Resumes
- **Endpoint:** `GET /api/resumes`
- **Query Params:** `skip=0`, `limit=50`, `status=completed`
- **Response (200 OK):** Paginated resume records.

### 3.3 Download Resume File
- **Endpoint:** `GET /api/resumes/{id}/download`
- **Response (200 OK):** Binary file stream with original filename.

### 3.4 Load 15 Synthetic Demo Resumes
- **Endpoint:** `POST /api/resumes/load-samples`
- **Response (200 OK):** Ingests and parses pre-packaged sample resumes.

---

## 4. Candidates Directory

### 4.1 List Candidates
- **Endpoint:** `GET /api/candidates`
- **Query Params:** `skip=0`, `limit=50`, `search=...`, `status=...`, `min_experience=...`
- **Response (200 OK):** Paginated candidates with skills and career metrics.

### 4.2 Get Candidate Detail
- **Endpoint:** `GET /api/candidates/{id}`
- **Response (200 OK):** Candidate profile, education history, work timeline, and skills.

### 4.3 Update Candidate Status
- **Endpoint:** `PUT /api/candidates/{id}`
- **Request Body:** `{"status": "shortlisted"}`
- **Response (200 OK):** Updated candidate record.

---

## 5. AI Matching & Ranking Engine

### 5.1 Run AI Matching Analysis
- **Endpoint:** `POST /api/matching/analyze`
- **Request Body:**
  ```json
  {
    "job_id": "job-uuid",
    "candidate_ids": ["cand-1", "cand-2"]
  }
  ```
  *(Omit `candidate_ids` to evaluate all candidates against the job)*
- **Response (200 OK):** List of computed matching analysis records.

### 5.2 Get Ranked Candidates Leaderboard
- **Endpoint:** `GET /api/matching/rankings/{job_id}`
- **Query Params:** `sort_by=overall_score|technical_score|semantic_score|experience_score|candidate_experience`, `sort_order=desc|asc`, `min_score=75`
- **Response (200 OK):** Ranked list of candidate analyses with full breakdown.

---

## 6. Multi-Candidate Comparison

### 6.1 Side-by-Side Comparison Matrix
- **Endpoint:** `POST /api/comparison/compare`
- **Request Body:**
  ```json
  {
    "job_id": "job-uuid",
    "candidate_ids": ["cand-1", "cand-2", "cand-3"],
    "use_llm": false
  }
  ```
- **Response (200 OK):** Side-by-side comparison matrix with skill overlap, score components, and strengths.

---

## 7. Shortlist & Recruiter Notes

### 7.1 Add to Shortlist
- **Endpoint:** `POST /api/shortlist` or `POST /api/shortlist/{job_id}/{candidate_id}`
- **Response (200 OK):** Shortlist record.

### 7.2 Check Shortlist Status
- **Endpoint:** `GET /api/shortlist/status/{job_id}/{candidate_id}`
- **Response (200 OK):** `{"is_shortlisted": true, "shortlist_id": "uuid"}`

### 7.3 Add Recruiter Note
- **Endpoint:** `POST /api/shortlist/{job_id}/{candidate_id}/notes`
- **Request Body:** `{"note": "Strong candidate for final round"}`

---

## 8. Analytics & Report Export

### 8.1 Analytics Dashboard Metrics
- **Endpoint:** `GET /api/analytics/dashboard`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Platform KPI counts (jobs, resumes, candidates, avg score).

### 8.2 Export Ranking Report
- **Endpoint:** `GET /api/analytics/reports/{job_id}?format=csv|xlsx|pdf`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Downloadable report stream.

---

## 9. AI Recruiter Chatbot

### 9.1 Chat with Assistant
- **Endpoint:** `POST /api/chatbot/chat`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "message": "Who is the top-ranked candidate for Lead AI Engineer?",
    "job_id": "job-uuid",
    "conversation_id": "session-123"
  }
  ```
- **Response (200 OK):** Fact-grounded recruiter answer, relevant database data, and starter chips.

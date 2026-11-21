# TalentMatch.ai — OpenAPI & REST API Specification

## 1. Specification Overview
- **Base URL**: `http://localhost:8000/api/v1` (or `https://api.talentmatch.ai/api/v1` in production)
- **Authentication**: HTTP Bearer Token (`Authorization: Bearer <access_token>`)
- **Format**: JSON (`Content-Type: application/json` or `multipart/form-data`)
- **Error Standard**: RFC 7807 Problem Details compliant structure

---

## 2. Authentication Endpoints

### 2.1 User Login
- **Method**: `POST`
- **Path**: `/auth/login`
- **Authentication**: None (Public)
- **Request Body**:
```json
{
  "email": "recruiter@talentmatch.ai",
  "password": "Recruiter@123456"
}
```
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "recruiter@talentmatch.ai",
    "full_name": "Demo Recruiter",
    "role": "recruiter",
    "organization": "TalentMatch AI Demo Corp"
  }
}
```
- **Errors**: `401 Unauthorized` (`"Invalid email or password"`)

---

## 3. Job Requisitions (`/jobs`)

### 3.1 List Jobs
- **Method**: `GET`
- **Path**: `/jobs`
- **Response (200 OK)**: Array of Job objects.

### 3.2 Create Job
- **Method**: `POST`
- **Path**: `/jobs`
- **Request Body**:
```json
{
  "title": "Senior Backend Engineer",
  "department": "Engineering",
  "description": "We are seeking a Senior Backend Engineer proficient in Python, FastAPI, Docker, and PostgreSQL...",
  "required_skills": ["python", "fastapi", "postgresql", "docker"],
  "preferred_skills": ["kubernetes", "redis", "aws"],
  "min_experience_years": 4.0,
  "education_level": "Bachelor"
}
```
- **Response (201 Created)**: Created Job object with assigned ID.

---

## 4. Resume Ingestion (`/resumes`)

### 4.1 Batch Upload Resumes (10+ files)
- **Method**: `POST`
- **Path**: `/resumes/batch-upload`
- **Content-Type**: `multipart/form-data`
- **Parameters**: `files`: Array of Binary Files (PDF or DOCX), `job_id`: Optional Integer
- **Security Validation**: Magic byte checks (`%PDF-`, `PK\x03\x04`), 10MB per file limit.
- **Response (200 OK)**:
```json
{
  "total_uploaded": 12,
  "successful_parses": 12,
  "failed_parses": 0,
  "candidates": [
    {
      "id": 101,
      "name": "Elena Rostova",
      "email": "elena.rostova@example.com",
      "total_experience_years": 4.5,
      "skills": ["python", "fastapi", "postgresql", "docker", "redis"],
      "highest_degree": "Bachelor"
    }
  ]
}
```

---

## 5. Explainable Matching & Ranking (`/matching`)

### 5.1 Run AI Matching
- **Method**: `POST`
- **Path**: `/matching/match`
- **Request Body**:
```json
{
  "job_id": 1,
  "candidate_ids": [101, 102, 103],
  "weights": {
    "semantic": 0.40,
    "skills": 0.30,
    "experience": 0.20,
    "education": 0.10
  }
}
```
- **Response (200 OK)**: Array of MatchRanking objects.

### 5.2 Get Ranked Leaderboard
- **Method**: `GET`
- **Path**: `/matching/rankings/{job_id}`
- **Response (200 OK)**:
```json
[
  {
    "id": 501,
    "job_id": 1,
    "candidate_id": 101,
    "candidate_name": "Elena Rostova",
    "match_percentage": 85.97,
    "semantic_score": 84.20,
    "skill_score": 80.00,
    "experience_score": 91.43,
    "education_score": 100.00,
    "matched_skills": ["python", "fastapi", "postgresql", "docker", "redis"],
    "missing_skills": ["kubernetes", "aws"],
    "candidate_experience": 4.5,
    "required_experience": 4.0,
    "candidate_degree": "Bachelor",
    "match_summary": "Strong technical alignment with 5 of 5 required skills and 4.5 verified years of experience."
  }
]
```

---

## 6. Agentic Recruitment Copilot (`/agent`)

### 6.1 Conversational Copilot Query
- **Method**: `POST`
- **Path**: `/agent/chat`
- **Request Body**:
```json
{
  "job_id": 1,
  "query": "Which candidate has the strongest cloud infrastructure background?"
}
```
- **Response (200 OK)**:
```json
{
  "response": "Based on verified resume evidence for Senior Backend Engineer, Elena Rostova and Marcus Vance possess the strongest cloud profiles. Marcus Vance demonstrated 3+ years managing AWS ECS and Kubernetes clusters...",
  "recommended_candidate_ids": [101, 104],
  "agent_name": "RecruiterCopilot-Agent"
}
```

### 6.2 Generate Targeted Interview Kit
- **Method**: `POST`
- **Path**: `/interview-kits/generate`
- **Request Body**:
```json
{
  "candidate_id": 101,
  "job_id": 1
}
```
- **Response (200 OK)**:
```json
{
  "candidate_id": 101,
  "job_id": 1,
  "questions": [
    {
      "category": "Skill Gap Verification",
      "topic": "Kubernetes",
      "question": "The JD requests Kubernetes container orchestration, which was not explicitly found on your resume. Can you describe your experience deploying containerized workloads to production?",
      "expected_signal": "Demonstrates understanding of pods, ingress controllers, and rolling deployments."
    }
  ]
}
```

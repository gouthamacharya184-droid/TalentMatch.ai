# TalentMatch.ai — Recruiter & Hiring Team User Guide

Welcome to **TalentMatch.ai**, an enterprise-grade agentic AI recruitment intelligence platform designed to transform bulk resume screening into an accurate, transparent, and explainable talent acquisition workflow.

---

## 1. Quick Start Workflow

```
1. Create Campaign ──> 2. Create Job & Approve Criteria ──> 3. Ingest Resumes in Bulk
                                                                       │
                                                                       ▼
6. Export Report <── 5. Generate Interview Kit <── 4. Screen, Rank & Simulate What-If
```

---

## 2. Platform Modules & Features

### 2.1 Recruitment Campaigns (`/campaigns`)
- **What it does:** Organizes hiring initiatives by department, headcount goals, and target completion dates.
- **How to use:**
  1. Click **New Campaign** from the top right.
  2. Enter the campaign title (e.g. *Q3 Global Backend Expansion*), target headcount, and department.
  3. Associate one or more job openings with the campaign to monitor aggregate progress.

### 2.2 Job Descriptions & AI Criteria Staging (`/jobs`)
- **What it does:** Allows recruiters to upload or author job descriptions. The `JobDescriptionAgent` automatically extracts title, seniority, mandatory skills, preferred skills, and experience benchmarks.
- **Criteria Approval Workflow:**
  1. Once a job is created, click **Review Criteria** on the job table row.
  2. Review the AI-extracted competencies and adjust scoring criteria weights (Required Skills 35%, Projects 25%, Experience 15%, Preferred 15%, Education 10%).
  3. Click **Approve Criteria & Unlock Screening** to finalize the benchmark.

### 2.3 Bulk Resume Upload (`/resumes/upload`)
- **What it does:** Asynchronously ingests single resumes or large batches (50–1,000+ files) across `.pdf`, `.docx`, `.doc`, and `.txt` formats.
- **Safety Features:** Automatically computes SHA-256 hashes to prevent duplicate processing. Isolates malformed or corrupted documents without halting batch execution.

### 2.4 AI Matching Engine (`/matching`)
- **What it does:** Evaluates candidate resumes against approved job criteria.
- **How to use:** Select a target job opening, select candidates or batches, and click **Run AI Matching**. The system executes semantic similarity, skill verification, project depth analysis, and experience relevance scoring.

### 2.5 Candidate Ranking Leaderboard (`/ranking`)
- **What it does:** Dynamic, multi-component leaderboard showing candidate match scores, verified skills, and experience tenure.
- **What-If Sensitivity Simulator:**
  1. Click **What-If Simulator** in the header.
  2. Adjust criteria weights (e.g., increase Relevant Projects from 25% to 40%).
  3. Click **Run Simulation** to preview instant score shifts and rank movements (▲ / ▼ deltas) across all candidates without altering official database records.
- **Exporting Reports:** Download executive reports in CSV, formatted Excel (`.xlsx`), or PDF.

### 2.6 Evidence Inspector (`/candidates` -> Inspect Modal)
- **What it does:** Grounds every evaluation in concrete resume text.
- **How to use:**
  1. Click **Inspect** on any candidate row.
  2. Switch to the **Evidence Inspector** tab.
  3. Filter by 6-tier classification:
     - *Explicitly Mentioned*
     - *Demonstrated in Project*
     - *Demonstrated Professionally*
     - *Weakly Inferred*
     - *Not Found*
  4. View the source document name, exact page number (e.g. *Page 2*), and quoted context.

### 2.7 Personalized Interview Intelligence (`/interview-kits`)
- **What it does:** Synthesizes candidate evidence and job criteria to formulate tailored interview kits.
- **Questions Provided:**
  - Technical deep-dive questions
  - Project architecture probes
  - Practical live coding challenges
  - **Claim-Verification Questions:** Specifically audits unsubstantiated claims on resumes with expected indicator checklists and 5-point evaluation rubrics.
- **Print / Export:** Click **Print Kit** to produce a clean printable interviewer dossier.

### 2.8 Recruiter Copilot Assistant (Floating Chatbot Widget)
- **What it does:** A conversational AI assistant connected directly to live recruitment database tools.
- **Example Queries:**
  - *"Show me top 5 candidates for Senior Full-Stack Engineer."*
  - *"Filter candidates who have demonstrated Docker in a professional project."*
  - *"Explain Alex Smith's score and what gaps were detected."*
  - *"Compare Alex Smith and Sarah Connor."*

### 2.9 Agent Observability & Telemetry (`/agent-activity`)
- **What it does:** Real-time monitoring dashboard for engineering and operations teams.
- **Metrics Tracked:** Total agent invocations, average latency in milliseconds, token consumption, and status traces across all 8 specialized agents.

---

## 3. Demo Credentials

Quick sign-in credentials (auto-filled by the buttons on the login screen):
- **Recruiter Demo:** `recruiter@talentmatch.ai` / `Recruiter@123456`
- **Admin Demo:** `admin@talentmatch.ai` / `Admin@123456`


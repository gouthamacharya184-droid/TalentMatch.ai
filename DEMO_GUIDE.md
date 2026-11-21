# LIVE TECHNICAL INTERVIEW DEMONSTRATION GUIDE

**Platform:** TalentMatch AI — AI-Based Resume Matching & Candidate Ranking System  
**Audience:** Technical Interviewers, Hiring Committee, Engineering Leadership  
**Demonstration Length:** 10 – 15 minutes  

---

## 1. Quick Startup Instructions

### Terminal 1: Backend API (FastAPI)
```bash
# Navigate to backend directory and start server
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Health Check: `http://127.0.0.1:8000/health`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### Terminal 2: Frontend Client (React + Vite)
```bash
# Navigate to frontend directory and start dev server
cd frontend
npm run dev
```
- Application Web Portal: `http://localhost:5173`

### Default Login Credentials
- **Role:** Tech Recruiter
- **Email:** `recruiter@talentmatch.ai`
- **Password:** `Recruiter@123456`
*(Or Super Admin: `admin@talentmatch.ai` / `Admin@123456`)*

---

## 2. Step-by-Step Live Demonstration Script

### STEP 1: Executive Dashboard & Platform Overview (1 min)
1. Log in with `recruiter@talentmatch.ai` / `Recruiter@123456`.
2. Direct attention to the **Analytics Dashboard**:
   - Total Active Jobs
   - Total Candidate Profiles Indexed
   - Average Match Score across Pipeline
   - Active Shortlists
   - Score distribution charts and hiring pipeline funnel.
3. *Key Interviewer Talking Point:* "The platform acts as a decision-support copilot for human recruiters, calculating reproducible matching scores grounded in extracted resume evidence."

---

### STEP 2: Job Description Management & NLP Skill Extraction (2 mins)
1. Click **"Jobs"** in the sidebar.
2. Select **"Create Job"** (or inspect an existing job like *Lead AI/NLP Engineer* or *Senior Full-Stack Engineer*).
3. Demonstrate document upload:
   - Click **"Upload JD File"** and upload `sample_jobs/Job_Senior_FullStack_Engineer.pdf` (or `.docx`).
   - Notice how the platform parses the document, auto-populates Title, Minimum Experience (4 yrs), Education (Bachelor's), and extracts technical competencies.
   - Show how the requirements modal allows recruiters to classify skills as **Mandatory** vs. **Preferred**.
4. Save the job and view its criteria.

---

### STEP 3: Bulk Resume Ingestion & Resilient Parsing (3 mins)
1. Click **"Upload Resumes"** in the sidebar.
2. **Option A (Instant Demo):** Click the purple **"Load 15 Demo Resumes"** button.
   - Demonstrates instant parallel ingestion of pre-packaged synthetic resumes (.PDF & .DOCX).
3. **Option B (Drag-and-Drop Batch):**
   - Open your file explorer to `sample_resumes/` or `test_resumes_50/`.
   - Drag and drop 10 to 15 PDF and DOCX files into the dropzone simultaneously.
   - Show the individual file progress bars, file size validation, and processing status badges (`Completed` / `Failed`).
4. **Demonstrate Error Boundary Isolation:**
   - Drag in `test_resumes_edge_cases/Edge_05_Oversized_16MB.pdf` or `Edge_01_Empty_Document.pdf`.
   - Point out that the oversized or empty document fails gracefully with an informative error badge while all valid resumes continue processing without crashing the batch.
   - Show the per-file **"Retry"** button.

---

### STEP 4: AI Matching & Transparent Scoring (3 mins)
1. Click **"AI Matching"** in the sidebar.
2. Select the target role: *Senior Full-Stack Engineer*.
3. Select candidates to analyze (or click **"Select All"**).
4. Click **"Run AI Matching Analysis"**.
5. Explain the **4-Component Weighted Scoring Formula**:
   - **40% Technical Skills:** Mandatory skills weighted 2x vs preferred 1x.
   - **30% Semantic Cosine Similarity:** Local Sentence Transformers (`all-MiniLM-L6-v2`) embeddings.
   - **20% Relevant Experience:** Non-overlapping career timeline compared to job minimum.
   - **10% Education:** Degree hierarchy alignment.
6. Emphasize: "No black-box hallucinations. Missing skills are deducted transparently. Demographics (names, emails) are excluded from embeddings to prevent bias."

---

### STEP 5: Dynamic Candidate Leaderboard & Detailed Analysis (3 mins)
1. Click **"Rankings"** in the sidebar.
2. Observe the ranked leaderboard sorted from highest to lowest match score:
   - Gold (#1), Silver (#2), Bronze (#3) badges.
   - Candidate Name and current designation (e.g. Alex Chen — Senior Full-Stack Developer).
   - Education degree, verified years of experience.
   - Overall match percentage with visual score bar.
   - 4-part sub-score breakdown: Tech (40), Semantic (30), Exp (20), Edu (10).
   - Matched skills count badge and missing skills badge.
3. Test interactive capabilities:
   - Filter by Minimum Score slider (e.g. 80%+).
   - Sort by Technical Score or Total Experience.
   - Search by skill keyword (e.g., "React" or "PostgreSQL").
   - Test the pagination controls (Next/Previous, 10 per page).
4. Click **"Inspect"** on Candidate #1 (Alex Chen):
   - **Overview Tab:** Contact details, education timeline, key projects.
   - **Skills Tab:** Verified skills alignment with exact vs. related badges, candidate strengths, and identified skill gaps.
   - **Interview Tab:** Tailored AI interview questions grounded in their specific projects.
   - **Notes Tab:** Type a recruiter note (e.g., *"Strong candidate for final tech panel"*) and save it.
   - Change candidate status to **"Shortlisted"** or **"Interview"**.

---

### STEP 6: Multi-Candidate Comparison & Report Export (2 mins)
1. Click **"Compare"** in the sidebar.
2. Select 2 to 4 candidates (e.g., Alex Chen, Marcus Vance, Samantha Miller).
3. Review the comparative matrix:
   - Visual bar chart comparing overall and component scores.
   - Skill overlap matrix highlighting shared skills and differentiating capabilities.
4. Export Reports:
   - Return to **Rankings** and click **CSV**, **Excel**, or **PDF**.
   - Download the file and show the structured report.

---

### STEP 7: TalentMatch AI Chatbot Copilot (1 min)
1. Click the floating blue chat bubble in the bottom-right corner.
2. Click a starter chip: *"How is the candidate score calculated?"* or ask: *"Who is the top candidate for this role?"*.
3. Show how the assistant answers using live database facts and explains the exact mathematical formula.

---

## 3. High-Value Technical Defense Questions & Answers

### Q1: Why not just use OpenAI / Claude API for the matching?
**Answer:** "External LLMs are expensive, introduce high network latency (2-5s per resume), pose privacy and compliance risks when transmitting candidate PII to third-party endpoints, and often hallucinate arbitrary scores without consistent mathematical reproducibility. TalentMatch AI executes local SentenceTransformers embeddings (`all-MiniLM-L6-v2`) in 2ms per comparison, keeping candidate data strictly within the organization's boundary with zero per-token API costs."

### Q2: How does the system prevent bias in AI ranking?
**Answer:** "First, demographic attributes (candidate name, gender, age, email, phone number, location, and photos) are strictly stripped from the semantic embedding target text. Second, the scoring formula relies exclusively on verified technical skill overlap, non-overlapping work duration, and degree credentials. Third, the system functions as a decision-support tool for human recruiters; automated rejections are disallowed."

### Q3: How do you prevent overlapping employment periods from inflating experience?
**Answer:** "In `ResumeParser._extract_experience`, all parsed employment date intervals are sorted chronologically and merged into non-overlapping continuous time ranges. If a candidate worked two roles concurrently between 2020 and 2022, they are credited with 2 years of experience rather than 4."

### Q4: How is bulk upload isolated against corrupt or malicious files?
**Answer:** "Every file uploaded via `POST /api/resumes/upload` is validated individually inside an isolated try-except boundary. We verify magic byte headers (`%PDF-` for PDF, `PK\x03\x04` for DOCX), enforce a 15MB file size limit, detect password encryption, and reject executable payloads disguised as documents. If 1 file out of a batch of 50 is corrupted, the other 49 process normally and only the corrupt file is tagged with an error badge."

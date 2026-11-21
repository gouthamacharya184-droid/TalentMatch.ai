# TalentMatch AI
### AI-Powered Resume Matching & Candidate Ranking Platform
**Product Tagline:** *Smarter Hiring. Better Matching. Faster Decisions.*  
**Developed for:** AVOM Consultants — AI-Based Resume Matching & Candidate Ranking System  
**Version:** 1.0.0 Production Release

---

## 1. Executive Summary & Product Overview

**TalentMatch AI** is a full-stack, enterprise-grade SaaS recruitment decision-support platform engineered to transform modern talent acquisition. By uniting natural language processing (NLP), semantic vector embeddings, and an evidence-based multi-factor weighted scoring algorithm, TalentMatch AI eliminates manual screening bottlenecks and enables recruiters to match, rank, compare, and shortlist candidates with speed, consistency, and complete mathematical transparency.

The platform requires **no mandatory paid API subscriptions** for its core intelligence; semantic matching runs locally and efficiently using open-source Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`) and Scikit-Learn TF-IDF vectorizers.

---

## 2. Key Capabilities & Three Core Demonstration Workflows

### DEMO 1 – Bulk Resume Upload & NLP Extraction
- Simultaneously upload **10 to 50 resumes** in one batch (.PDF, .DOCX, .TXT).
- Drag-and-drop file ingestion, file validation, duplicate file detection, individual and batch progress tracking.
- Automated extraction of personal contact details, educational degrees, institutions, graduation years, career experience duration, and categorized technical skills.
- Includes a 1-click **"Load 15 Demo Resumes"** feature with 15 pre-generated PDF and DOCX candidate profiles for immediate demonstration.

### DEMO 2 – Semantic AI Matching Engine
- Select any active job description (or upload a new JD document in PDF/DOCX/TXT).
- NLP analysis extracts mandatory vs. preferred skills and career criteria.
- 4-Component Weighted Scoring Model (0 – 100 points):
  - **Technical Skill Match (40%)**: Verified exact and related skill matches vs. mandatory and preferred requirements.
  - **Semantic Similarity (30%)**: Cosine similarity of contextual document embeddings using Sentence Transformers (`all-MiniLM-L6-v2`).
  - **Relevant Experience (20%)**: Stated years of experience compared against job minimum experience.
  - **Education & Qualifications (10%)**: Degree level alignment (Ph.D., Master's, Bachelor's).
- 100% explainable results: surfaces matched skills with confidence scores and resume evidence, identifies missing mandatory qualifications, and computes candidate strengths and skill gaps.

### DEMO 3 – Candidate Ranking, Comparison & Shortlisting
- **Candidate Ranking Leaderboard**: Automatically ranks candidates from highest to lowest matching score with filters for score ranges, experience, skills, and application status.
- **Detailed Candidate Analysis Modal**: Deep-dive profile view, score breakdowns, resume viewer/downloader, recruiter private notes, and status updates.
- **Side-by-Side Multi-Candidate Comparison**: Compare 2 to 5 candidates across all skill dimensions, strengths, and qualification gaps in a comparative matrix.
- **AI Interview Question Generator**: Automatically produces tailored technical, practical coding, project-based, and experience-based interview questions with suggested evaluation criteria.
- **Exportable Analytics & Reports**: One-click download of recruitment reports in **CSV**, **Excel (.xlsx)**, and **PDF** formats.

### DEMO 4 – TalentMatch AI Floating Chatbot Copilot
- **Always-Available Recruiter Assistant**: Fixed floating circular widget positioned bottom-right on every authenticated dashboard view.
- **Real-Data Grounded Intelligence**: Directly queries database models (live candidates, jobs, scores, metrics, skills) — never hallucinates fake data.
- **Contextual Copilot**: Explains candidate scores (40% skills, 30% embeddings, 20% experience, 10% education), identifies missing candidate skills, compares top candidates, and summarizes dashboard analytics.
- **Dual Engine Architecture**: Powers real-time reasoning with configured LLMs (Google Gemini, OpenAI, Groq) with an instant, deterministic rule-based fallback if offline or quota-limited.
- **Enterprise Features**: 1-click suggested prompts, rich markdown rendering, response copy-to-clipboard, conversation clearing, and ethical bias guardrails.

---

## 3. Technology Stack

### Frontend
- **Framework:** React 18, Vite, TypeScript
- **Styling:** Tailwind CSS (Enterprise "Premium White & Blue" design system)
- **Icons:** Lucide React
- **Data Visualizations:** Recharts (responsive bar charts, score distributions, skill availability)
- **Routing & State:** React Router v6, Axios with JWT interceptors, Context API
- **Animations:** Lightweight CSS keyframes and transitions

### Backend
- **Framework:** Python 3.12, FastAPI (high-concurrency asynchronous REST APIs)
- **Data Validation & Schemas:** Pydantic v2
- **ORM & Database:** SQLAlchemy 2.0, Alembic database migrations
- **Databases:** PostgreSQL (production) & SQLite (local development zero-config option)
- **Authentication & Security:** Argon2 / Bcrypt password hashing, PyJWT bearer token authentication with role-based access control (Super Admin, Recruiter, Hiring Manager)

### AI, NLP & Document Parsing
- **Semantic Embeddings:** Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`) with PyTorch
- **Semantic Fallback:** Scikit-learn TF-IDF n-gram vectorizer with cosine similarity
- **NLP & Taxonomy:** Custom taxonomy dictionary covering 1,200+ technical skills and abbreviations
- **Document Extractors:** PyMuPDF (`fitz`), python-docx, reportlab

---

## 4. Repository & Project Structure

```text
TalentMatch-AI/
├── backend/
│   ├── alembic/                # Database migrations
│   │   ├── versions/           # Migration version scripts
│   │   └── env.py              # Alembic environment runner
│   ├── app/
│   │   ├── ai_engine/          # Core AI matching, embeddings, skill dictionary
│   │   ├── api/                # REST API routers (auth, jobs, resumes, matching, etc.)
│   │   ├── core/               # Configuration, security, JWT helpers
│   │   ├── database/           # Database session engine and seed data
│   │   ├── models/             # Normalized SQLAlchemy relational models
│   │   ├── parsers/            # PDF and DOCX document extractors
│   │   ├── schemas/            # Pydantic input/output schemas
│   │   ├── services/           # Business logic layer
│   │   └── main.py             # FastAPI entrypoint and lifespan management
│   ├── tests/                  # Automated test suite (13 integration tests)
│   ├── alembic.ini             # Alembic configuration
│   ├── Dockerfile              # Backend multi-stage Dockerfile
│   └── requirements.txt        # Python dependencies
│
├── frontend/
│   ├── public/                 # Static assets
│   ├── src/
│   │   ├── components/         # Reusable UI components (CandidateDetailModal, etc.)
│   │   ├── context/            # AuthContext and session state
│   │   ├── layouts/            # DashboardLayout (Sidebar, Topbar, Navigation)
│   │   ├── pages/              # 15 Complete application pages
│   │   ├── services/           # Axios API client functions
│   │   ├── types/              # TypeScript interface definitions
│   │   ├── App.tsx             # Route definitions and protected route wrappers
│   │   └── main.tsx            # React DOM mounting
│   ├── Dockerfile              # Frontend production Dockerfile
│   ├── nginx.conf              # Nginx reverse proxy configuration
│   ├── package.json            # NPM scripts and dependencies
│   ├── tailwind.config.js      # Custom theme styling
│   └── vite.config.ts          # Vite build config
│
├── sample_resumes/             # 15 realistic candidate resumes (10 PDF, 5 DOCX)
├── sample_jobs/                # Sample job descriptions (PDF, DOCX, TXT)
├── scripts/                    # Test generation and utility scripts
├── storage/
│   └── uploads/                # Managed file storage directory
├── deployment/                 # Deployment templates & Nginx proxy configs
├── docker-compose.yml          # Production multi-container orchestration
├── .env.example                # Example environment configuration
├── LICENSE                     # MIT License
└── README.md                   # Complete documentation
```

---

## 5. Quick Start & Local Setup Instructions

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ and npm
- Git

---

### Step 1: Clone and Configure Environment

```bash
git clone https://github.com/avom-consultants/TalentMatch-AI.git
cd TalentMatch-AI

# Copy environment template
cp .env.example .env
```

---

### Step 2: Backend Setup & Execution

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations and seed default data:
   ```bash
   alembic upgrade head
   ```

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

The backend API will be live at: `http://localhost:8000`  
Interactive Swagger API documentation: `http://localhost:8000/docs`

---

### Step 3: Frontend Setup & Execution

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The web application will be accessible at: `http://localhost:5173`

---

### Step 4: Login Credentials (Pre-Seeded)

The database is pre-seeded with realistic roles and candidates:

| Role | Email | Password |
|---|---|---|
| **Super Admin** | `admin@talentmatch.ai` | `Admin@123456` |
| **Senior Recruiter** | `recruiter@talentmatch.ai` | `Recruiter@123456` |

*Recruiters can also freely register new accounts on the registration page.*

---

## 6. Docker Containerized Deployment

To deploy the entire production stack (PostgreSQL 16, FastAPI Backend, and Nginx-served React Frontend) with one command:

```bash
docker compose up --build -d
```

- **Frontend Application:** `http://localhost:80` (or `http://localhost:5173`)
- **Backend API:** `http://localhost:8000`
- **Swagger Documentation:** `http://localhost:8000/docs`
- **PostgreSQL Database:** `localhost:5432`

To shut down:
```bash
docker compose down
```

---

## 7. Automated Test Suite

TalentMatch AI includes a comprehensive automated integration and validation test suite covering authentication, job CRUD, document upload, bulk resume parsing, AI semantic matching mathematical boundaries (0–100), ranking consistency, candidate comparisons, shortlisting, recruiter notes, and report exports.

To execute the test suite:

```bash
cd backend
python -m pytest tests/ -v
```

**Test Results:**
```text
tests/test_full_suite.py::test_health_and_root PASSED                    [  7%]
tests/test_full_suite.py::test_auth_login PASSED                         [ 15%]
tests/test_full_suite.py::test_get_dashboard_analytics PASSED            [ 23%]
tests/test_full_suite.py::test_job_crud_and_requirements PASSED          [ 30%]
tests/test_full_suite.py::test_candidates_and_rankings PASSED            [ 38%]
tests/test_full_suite.py::test_candidate_comparison PASSED               [ 46%]
tests/test_full_suite.py::test_shortlist_and_notes PASSED                [ 53%]
tests/test_full_suite.py::test_report_exports PASSED                     [ 61%]
tests/test_resume_upload_and_ai.py::test_jd_upload_document PASSED       [ 69%]
tests/test_resume_upload_and_ai.py::test_load_sample_batch_resumes PASSED [ 76%]
tests/test_resume_upload_and_ai.py::test_ai_matching_and_scoring_constraints PASSED [ 84%]
tests/test_resume_upload_and_ai.py::test_ranking_sort_order PASSED       [ 92%]
tests/test_resume_upload_and_ai.py::test_single_candidate_details_and_notes PASSED [100%]

============================= 13 passed in 64s =============================
```

---

## 8. Complete Application Navigation Map

All 14 pages are fully functional, interactive, and connected to live backend APIs:

1. **Dashboard (`/`)**: Recruitment KPIs, matching score distributions, top candidates, recent jobs.
2. **Job Descriptions (`/jobs`)**: Create jobs, upload JD files (PDF/DOCX/TXT), edit extracted requirements, delete jobs.
3. **Resume Upload (`/resumes/upload`)**: Drag-and-drop bulk upload for 10–50 resumes, individual parsing status, 1-click 15 demo resume ingestion.
4. **AI Matching (`/matching`)**: Select target job description and candidates, execute multi-factor AI matching pipeline.
5. **Candidates (`/candidates`)**: Complete candidate registry, skills tags, status updates, candidate deletion.
6. **Candidate Ranking (`/ranking`)**: Dynamic leaderboard sorted by matching scores, score filters, export to CSV/XLSX/PDF.
7. **Compare Candidates (`/compare`)**: Side-by-side comparison matrix for 2–5 candidates.
8. **Shortlisted Candidates (`/shortlist`)**: Hiring pipeline tracking (Shortlisted, Under Review, Interview, Hired, Rejected).
9. **Analytics & Reports (`/analytics`)**: Visual recruitment metrics, score spreads, downloadable reports.
10. **Analysis History (`/history`)**: Historical matching audit logs and previous ranking results.
11. **User Profile (`/profile`)**: Manage recruiter profile, name, password, and active role.
12. **Settings (`/settings`)**: Configurable scoring weights, threshold tolerances, and system preferences.
13. **Security & Privacy (`/security`)**: Security audit logs, active sessions, and data deletion controls.
14. **Authentication (`/login`, `/register`)**: JWT registration, login, logout, and protected routing.

---

## 9. Final Acceptance Checklist

- [x] Recruiter can register and log in securely.
- [x] Recruiter can create and save a job description.
- [x] Recruiter can upload a job description document (.PDF, .DOCX, .TXT).
- [x] AI extracts job requirements automatically.
- [x] Recruiter can review and edit extracted requirements.
- [x] Recruiter can upload at least 10–50 resumes simultaneously.
- [x] PDF and DOCX files are parsed with text extraction.
- [x] Candidate information (contact, education, skills, experience) is extracted.
- [x] Recruiter can correct candidate details.
- [x] AI performs semantic matching using `all-MiniLM-L6-v2` and cosine similarity.
- [x] AI identifies exact matches, related matches, and missing skills.
- [x] Matching scores are strictly calculated from 0 to 100 points.
- [x] Every score provides explainable evidence and strengths/gaps.
- [x] Candidates are automatically ranked from highest to lowest.
- [x] Recruiter can open detailed candidate profile and AI analysis.
- [x] Recruiter can compare multiple candidates side-by-side.
- [x] Recruiter can shortlist candidates and record private screening notes.
- [x] Recruiter can export results to CSV, Excel, and PDF.
- [x] Dashboard analytics query actual database records.
- [x] Alembic database migrations and PostgreSQL support.
- [x] Dockerfile and Docker Compose configurations included.
- [x] Automated test suite executed and verified (13/13 passing).
- [x] Production build verified.
- [x] One complete deliverable ZIP archive generated.

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.


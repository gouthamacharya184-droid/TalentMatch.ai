# TalentMatch.ai — Enterprise Agentic Recruitment Platform
### Production-Grade AI Resume Screening, Candidate Ranking & Decision Intelligence

[![CI/CD Pipeline](https://github.com/gouthamacharya184-droid/TalentMatch.ai/actions/workflows/ci.yml/badge.svg)](https://github.com/gouthamacharya184-droid/TalentMatch.ai/actions)
[![Pytest Suite](https://img.shields.io/badge/pytest-60%2F60%20passed-brightgreen.svg)](docs/TEST_REPORT.md)
[![TypeScript](https://img.shields.io/badge/typescript-%5E5.7-blue.svg)](frontend/package.json)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](backend/requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](backend/app/main.py)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](frontend/src/App.tsx)
[![Vercel Ready](https://img.shields.io/badge/Vercel-SPA%20Ready-black.svg)](frontend/vercel.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Executive Summary & Product Architecture

**TalentMatch.ai** is an enterprise-grade agentic AI recruitment intelligence platform designed to eliminate recruiter screening bottlenecks, eradicate keyword ATS bias, and accelerate technical hiring with **100% explainable mathematical rigor**.

Unlike basic ATS keyword matchers or black-box LLM wrappers, TalentMatch.ai executes an on-premise, four-pillar hybrid scoring model powered by **Sentence Transformers (`all-MiniLM-L6-v2`)**, a 1,200+ entry taxonomic skill dictionary, and non-overlapping timeline interval verification.

```
                              TALENTMATCH.AI ARCHITECTURE
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │  REACT 19 SPA (Vite 6 + Tailwind CSS v4 + Lucide + Recharts)                          │
 │  • Lazy-Loaded Route Bundles (< 25 kB per page)   • Dynamic VITE_API_URL Remote Sync   │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ HTTP REST / JWT Bearer
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │  FASTAPI BACKEND (Python 3.11+ / Pydantic v2 / Asyncio Concurrency)                    │
 │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌────────────────────────┐  │
 │  │ Secure Upload & Parser  │  │ Hybrid Scoring Engine   │  │ Agent Orchestrator     │  │
 │  │ • Magic Bytes (%PDF, PK)│  │ • 40% MiniLM Embedding  │  │ • Recruitment Copilot  │  │
 │  │ • Non-overlapping Dates │  │ • 30% Taxonomic Skills  │  │ • 5-Q Interview Kits   │  │
 │  │ • Demographic Blinding  │  │ • 20% Non-Linear Exp    │  │ • Evidence Extraction  │  │
 │  │ • PDFJS & Bomb Defense  │  │ • 10% Degree Hierarchy  │  │ • Audit Log Monitor    │  │
 │  └─────────────────────────┘  └─────────────────────────┘  └────────────────────────┘  │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ SQLAlchemy 2.0 ORM
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │  ENTERPRISE PERSISTENCE LAYER                                                          │
 │  • SQLite 3 (WAL Mode, zero-config local) / PostgreSQL 15+ (Production Pool)           │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Documentation Suite

| Document | Purpose & Contents | Link |
| :--- | :--- | :--- |
| **Product Requirements (PRD)** | Problem statement, user personas, user stories, functional & non-functional specs | [Read PRD](docs/PRD.md) |
| **System Architecture** | C4 Level 1 & 2 diagrams, batch ingestion sequence, AI copilot sequence, stack rationale | [Read Architecture](docs/ARCHITECTURE.md) |
| **Explainable Matching Algorithm** | Mathematical formulas, 40/30/20/10 weights, step-by-step worked example, interview defense | [Read Algorithm](docs/MATCHING_ALGORITHM.md) |
| **Database Architecture** | Mermaid ERD, table definitions, column types, foreign keys, indexing, GDPR deletion | [Read Database](docs/DATABASE.md) |
| **OpenAPI & REST API** | Endpoints specification with request/response payloads, authentication, and error codes | [Read API Docs](docs/API.md) |
| **Security & Privacy** | STRIDE threat model, OWASP Top 10 mitigations, file upload hardening, EEOC fair hiring | [Read Security](docs/SECURITY.md) |
| **Test Execution Report** | 60/60 automated pytest integration test verification and coverage breakdown | [Read Test Report](docs/TEST_REPORT.md) |

---

## 3. Explainable 4-Pillar Matching Formula

Every candidate score $S_{\text{final}} \in [0, 100\%]$ is completely decomposed:

$$S_{\text{final}} = (0.40 \times S_{\text{semantic}}) + (0.30 \times S_{\text{skills}}) + (0.20 \times S_{\text{experience}}) + (0.10 \times S_{\text{education}})$$

1. **Semantic Similarity ($S_{\text{semantic}}$ - 40%)**: Cosine similarity between candidate and job description embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors) with SHA-256 LRU vector caching.
2. **Taxonomic Skills ($S_{\text{skills}}$ - 30%)**: Normalized skill extraction using alias mapping (`k8s` $\rightarrow$ `kubernetes`, `postgres` $\rightarrow$ `postgresql`), weighted 70% mandatory and 30% preferred.
3. **Calibrated Experience ($S_{\text{experience}}$ - 20%)**: Fractional monthly interval merging to eliminate double-counting of concurrent roles, with sub-linear partial credit $(\text{cand}/\text{req})^{0.85}$ and over-qualification dampening.
4. **Educational Alignment ($S_{\text{education}}$ - 10%)**: Tiered degree hierarchy (PhD, Master's, Bachelor's, Associate/Diploma, None) with compensation for senior experience.

> **Worked Example with Real Numbers:** See [docs/MATCHING_ALGORITHM.md](docs/MATCHING_ALGORITHM.md) for a full mathematical trace of a Senior Full-Stack Engineer candidate scoring 85.97%.

---

## 4. Quickstart (< 5 Commands)

### Prerequisites
- Python 3.11 or 3.12
- Node.js 18+ and npm
- Git

```bash
# 1. Clone repository
git clone https://github.com/gouthamacharya184-droid/TalentMatch.ai.git
cd TalentMatch.ai

# 2. Setup and run Backend (Terminal 1)
python -m venv backend/venv
# On Windows:
.\backend\venv\Scripts\Activate.ps1
# On macOS/Linux: source backend/venv/bin/activate
pip install -r backend/requirements.txt
$env:PYTHONPATH="backend"; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. Setup and run Frontend (Terminal 2)
cd frontend
npm install
npm run dev

# 4. Open in browser
# http://localhost:5173
```

### Pre-Seeded Quick Test Credentials

| Role | Email | Password | UI Shortcut |
| :--- | :--- | :--- | :--- |
| **Senior Recruiter** | `recruiter@talentmatch.ai` | `Recruiter@123456` | Click **"Fill Recruiter Demo"** |
| **Platform Administrator** | `admin@talentmatch.ai` | `Admin@123456` | Click **"Fill Admin Demo"** |

---

## 5. Recruiter Demo Walkthrough Script

1. **Sign In**: Navigate to `http://localhost:5173/login` and click **"Fill Recruiter Demo"** $\rightarrow$ **"Sign In to Workspace"**.
2. **Review Campaign & Jobs**: Go to **Jobs** (`/jobs`). View the pre-seeded *Senior Backend Engineer* and *Full Stack Cloud Architect* requisitions or click **"Create Requisition"** to paste a new job description.
3. **Batch Resume Ingestion**: Navigate to **Upload Resumes** (`/resumes/upload`). Drop 10+ PDF/DOCX resumes or click **"Load 15 Demo Resumes"** to ingest real candidates with non-overlapping experience and skill profiles in 3 seconds.
4. **Run AI Matching**: Open **AI Matching** (`/matching`). Select your target job and click **"Execute Multi-Factor Match"**. Watch the SentenceTransformer embedding engine compute dense similarity and skill overlaps in real time.
5. **Inspect Ranked Leaderboard**: Open **Ranking** (`/ranking`). Filter by minimum score or experience. Click on any candidate to inspect their **Candidate Dossier Modal** with exact score breakdowns, green matched skill pills, amber missing skill pills, and verbatim resume citations.
6. **Side-by-Side Comparison**: Select 2–3 candidates and navigate to **Compare Candidates** (`/compare`) to inspect their skill matrices side by side.
7. **AI Recruitment Copilot**: Click the floating blue robot in the bottom-right corner to interact with the grounded Recruiter Copilot. Ask: *"Who has the strongest Kubernetes background?"* or *"Summarize Elena's qualifications"*.
8. **Generate Interview Kit**: From the candidate modal or **Interview Intelligence** (`/interview-kits`), click **"Generate Interview Kit"** to produce 5 custom behavioral and technical questions targeting verified skill gaps.

---

## 6. Vercel & Cloud Deployment Guide

TalentMatch.ai is engineered following **Option A (Enterprise Decoupled Deployment)**:
- **Frontend SPA**: Deployed to Vercel with high-speed global edge CDN distribution, asset caching, and client-side route rewrites.
- **Backend API & ML Engine**: Deployed to Render, Railway, AWS EC2, or Docker Container with persistent GPU/CPU resources for SentenceTransformers (`torch`).

### Deploying Frontend to Vercel:
1. Connect this GitHub repository (`https://github.com/gouthamacharya184-droid/TalentMatch.ai.git`) to [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Set **Framework Preset** to `Vite`.
4. Add the Environment Variable:
   - `VITE_API_URL` = `https://your-backend-api-domain.com` (e.g. Render/Railway URL)
5. Click **Deploy**. Vercel will build the frontend using `npm run build` and serve via `frontend/vercel.json`.

---

## 7. Running Tests & Quality Verification

TalentMatch.ai includes a comprehensive test suite of **60 passing automated tests**:

```bash
# Run backend pytest suite with coverage
$env:PYTHONPATH="backend"
python -m pytest backend/tests -v

# Run frontend type-check and production build
npm --prefix frontend run build

# Run frontend linter
npm --prefix frontend run lint
```

**Pytest Execution Summary:**
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0
collected 60 items

backend\tests\test_agentic_platform.py ......                            [ 10%]
backend\tests\test_audit_fixes_regression.py .....                       [ 18%]
backend\tests\test_audit_validation.py ........                          [ 31%]
backend\tests\test_bulk_upload_comprehensive.py ..................       [ 61%]
backend\tests\test_chatbot.py ..........                                 [ 78%]
backend\tests\test_full_suite.py ........                                [ 91%]
backend\tests\test_resume_upload_and_ai.py .....                         [100%]

============================= 60 passed in 54.06s =============================
```

---

## 8. Interview Defense FAQ

### Q1: Why not rely purely on LLM prompts for scoring?
> **Answer**: Unbounded LLMs (like raw GPT-4) suffer from stochastic score drift, hallucinate credentials not present on the resume, are easily manipulated by prompt injection (white font on PDFs), and cost orders of magnitude more time and money. Our local hybrid model computes scores deterministically in milliseconds with zero prompt injection risk and complete mathematical explainability.

### Q2: How does the system handle concurrent jobs on resumes?
> **Answer**: Our date extractor parses text and numeric month representations into fractional years ($2020 + \frac{\text{month}-1}{12}$). Overlapping timeline intervals $[t_1, t_2]$ and $[t_3, t_4]$ where $t_3 \le t_2$ are unified into $[t_1, \max(t_2, t_4)]$ using geometric interval scheduling. This prevents a candidate working two concurrent contracts from artificially doubling their actual chronological experience.

### Q3: How do you defend against algorithmic hiring bias?
> **Answer**: We implement automated demographic blinding—scrubbing names, gender indicators, addresses, and graduation dates before vectorization. Additionally, every score is decomposed into audited technical metrics (skills, non-overlapping experience, degrees) ensuring complete adverse impact defensibility under EEOC guidelines.

---

## 9. License
This project is open-sourced under the **MIT License**. See [LICENSE](LICENSE) for details.

# TalentMatch.ai

> Enterprise agentic AI recruitment intelligence platform for explainable candidate screening, ranking, multi-agent evaluation, and deterministic hiring decisions.

TalentMatch.ai combines semantic similarity, taxonomic skill verification, non-overlapping timeline calculations, degree alignment, and anti-hallucination guardrails into a 100% explainable, deterministic hiring copilot.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Client["Frontend Client (Vite + React + Tailwind + Lucide)"]
        SPA["Single-Page Application"]
        A11y["Accessible UI (WCAG 2.2 AA)"]
        Theme["Theme & Design System"]
    end

    subgraph Edge["Reverse Proxy / Edge / API Gateway"]
        CORS["CORS & Headers (HSTS, CSP, X-Frame)"]
        RateLimit["Sliding-Window Rate Limiter"]
        ReqID["X-Request-ID & Latency Tracker"]
    end

    subgraph Backend["FastAPI Enterprise Application"]
        Routers["Modular API Routers (Auth, Candidates, Jobs, Matching, Copilot)"]
        Deps["Dependency Injection & Auth Guards (RBAC)"]
        
        subgraph Agents["Multi-Agent AI Intelligence Engine"]
            Orchestrator["Agent Orchestrator"]
            ResumeAgent["Resume Parser & Entity Extractor"]
            SkillAgent["Taxonomic Skill Verifier"]
            ExpAgent["Timeline & Overlap Calculator"]
            MatchAgent["Deterministic Matching Engine"]
            Copilot["Copilot & Interview Kit Agent"]
            Guardrails["Prompt Injection & Fencing Layer"]
        end

        subgraph Core["Core Security & Data Services"]
            TokenRevoke["RevokedToken Persistence Layer"]
            PassHashing["Argon2id / PBKDF2 Password Hashing"]
            DocParsers["PDF / DOCX Chunked Stream Parsers"]
        end
    end

    subgraph Data["Persistence & Storage Layer"]
        DB[("PostgreSQL (Production) / SQLite (Dev)")]
        BlobStore[("Vercel Blob / Local Storage")]
    end

    subgraph External["External AI Provider"]
        Gemini["Google Gemini (gemini-2.5-flash)"]
        Groq["Groq Llama-3-70B (Fallback)"]
    end

    SPA --> CORS
    CORS --> RateLimit
    RateLimit --> ReqID
    ReqID --> Routers
    Routers --> Deps
    Deps --> Core
    Routers --> Agents
    Guardrails --> External
    Agents --> Guardrails
    Core --> DB
    DocParsers --> BlobStore
```

---

## End-to-End User & Agent Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / Hiring Lead
    participant Web as React Web Client
    participant API as FastAPI Backend (api/deps)
    participant Engine as AI Matching Engine
    participant LLM as Google Gemini / Groq
    participant DB as Relational Database

    Recruiter->>Web: Log in (Email/Password)
    Web->>API: POST /api/auth/login (Rate-limited: 15/min)
    API->>DB: Verify credentials & issue JWT (Access + Refresh)
    API-->>Web: Set Secure Tokens & User Profile

    Recruiter->>Web: Upload Candidate Resumes (PDF / DOCX)
    Web->>API: POST /api/resumes/upload (Rate-limited, Memory-capped)
    API->>API: Stream chunk parse text, extract entities & skills
    API->>DB: Persist Candidate & Raw Resume

    Recruiter->>Web: Select Job Opening & Trigger Match
    Web->>API: POST /api/matching/match/{job_id}
    API->>Engine: Deterministic Match (Skills + Timeline + Degree)
    Engine->>LLM: Explainable Insight Generation (Prompt-fenced)
    LLM-->>Engine: Structured Synthesis & Recommendations
    Engine->>DB: Store Match Score & Radar Dimensions
    API-->>Web: Real-Time Radar Matrix & Explainable Gap Analysis

    Recruiter->>Web: Ask Copilot / Generate Interview Kit
    Web->>API: POST /api/chatbot/chat
    API->>Engine: Sanitize input & Intent Classification
    Engine->>LLM: Generate Tailored Question Set (Behavioral + Technical)
    API-->>Web: Streamed Questions, Star Rubric & Red Flag Alerts
```

---

## Production Readiness & Security Hardening

The application has undergone a comprehensive full-stack production audit covering 15 mission-critical areas:

| Area | Production Capability | Implementation |
| :--- | :--- | :--- |
| **Authentication & RBAC** | Persistent token invalidation & Replay-proof resets | DB-backed `RevokedToken` table with in-memory fast cache; cryptographically unique UUID `jti` on password reset tokens. |
| **API Rate Limiting** | Tiered sliding-window rate limiting | Memory-bounded rate limiter protecting auth (`15/min`), resume uploads (`30/min`), and LLM endpoints (`45/min`). |
| **AI Safety & Guardrails** | Prompt injection defense & hallucination fencing | `sanitize_user_input` and `fence_document_context` filter system overrides, jailbreaks, and delimiter escapes. 32-case deterministic evaluation test suite. |
| **Observability** | Request tracing & latency headers | Every request receives an `X-Request-ID` correlation ID and `X-Response-Time` microsecond timing header. Production 500 errors are masked to prevent leakages. |
| **Memory & Performance** | Streamed, chunked file parsing | Upload handler enforces `MAX_FILE_SIZE_MB` with bounded 64KB read chunks to prevent memory denial-of-service. |
| **Containerization** | Minimal multi-stage non-root container | Multi-stage Dockerfile running as non-privileged `appuser:appgroup` with production gunicorn/uvicorn worker configurations. |
| **Disaster Recovery** | Point-in-time recovery & automated backups | `scripts/backup_database.py` with gzip compression, SHA-256 integrity verification, and 7-day retention management. |
| **CI/CD** | Automated security and quality gate | GitHub Actions workflow executing Python 3.12, Bandit AST security scanning, Ruff linter, full pytest suite, and frontend build checks. |

---

## Quickstart (Local Development)

### 1. Prerequisites
- **Python**: 3.11 or 3.12+
- **Node.js**: 20+ and npm
- **Docker & Docker Compose** (Optional, for containerized run)

### 2. Backend Setup
```bash
# Clone repository
git clone https://github.com/your-org/TalentMatch.ai.git
cd TalentMatch.ai

# Create and activate virtual environment
python -m venv backend/venv

# Windows:
.\backend\venv\Scripts\Activate.ps1
# macOS/Linux:
# source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations and seed default data
python backend/app/database/seed.py

# Launch FastAPI development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API runs at `http://127.0.0.1:8000` (Interactive OpenAPI Swagger at `http://127.0.0.1:8000/docs`).

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
UI runs at `http://localhost:5173`.

### Pre-Seeded Demo Accounts
- **Recruiter**: `recruiter@talentmatch.ai` / `Recruiter@123456`
- **Admin**: `admin@talentmatch.ai` / `Admin@123456`

---

## Docker Compose (Production-Ready Dev/Stage Stack)

You can run the full stack (FastAPI Backend + PostgreSQL 16) with a single command:

```bash
docker-compose up -d --build
```

- **Backend**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **PostgreSQL**: `localhost:5432` (`talentmatch_db`)

To view logs or shut down:
```bash
docker-compose logs -f app
docker-compose down -v  # To stop and remove volumes
```

---

## Deploy to Vercel (Single Full-Stack Project)

TalentMatch.ai is pre-configured to deploy to Vercel as a unified full-stack application (Vite SPA frontend + Python serverless API functions via `api/index.py`).

### 1. Deploy via Vercel Dashboard
1. Import this repository into Vercel.
2. Leave **Root Directory** as `./` (repo root).
3. The `vercel.json` automatically configures:
   - **Build Command**: `npm --prefix frontend install && npm --prefix frontend run build`
   - **Output Directory**: `frontend/dist`
   - **API Routes**: `/api/(.*)` rewrites to `api/index.py` (FastAPI ASGI)

### 2. Required Environment Variables

| Variable | Environment | Description | Example |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Production** | PostgreSQL connection string with SSL | `postgresql://user:pass@ep-xyz.neon.tech/talentmatch?sslmode=require` |
| `SECRET_KEY` | **Production** | Random 32+ character JWT signing key | `openssl rand -hex 32` |
| `ENVIRONMENT` | **Production** | Set to `production` for strict security | `production` |
| `DEBUG` | **Production** | Disable debug mode in production | `False` |
| `BLOB_READ_WRITE_TOKEN` | Optional | Vercel Blob token for cloud file storage | Auto-set when attaching Vercel Blob store |
| `LLM_API_KEY` | Optional | Google Gemini API key for AI features | `AIzaSy...` |
| `LLM_MODEL` | Optional | Model identifier (defaults to `gemini-2.5-flash`) | `gemini-2.5-flash` |
| `ALLOWED_ORIGINS` | Optional | Extra CORS origins (same-origin works by default) | `https://talentmatch.example.com` |

---

## Database Backup & Disaster Recovery

Run automated local or remote backups:
```bash
# SQLite (Development)
python scripts/backup_database.py --sqlite-db talentmatch.db --backup-dir ./backups

# PostgreSQL (Production)
python scripts/backup_database.py --db-url "postgresql://user:password@localhost:5432/talentmatch" --backup-dir ./backups
```
For complete RTO, RPO, and failover runbooks, see [DISASTER_RECOVERY.md](docs/DISASTER_RECOVERY.md).

---

## Quality & Security Verification Commands

```bash
# 1. Run Python static analysis & style checks
backend/venv/Scripts/ruff check backend/app

# 2. Run Python AST security audit (Bandit)
backend/venv/Scripts/bandit -r backend/app -ll -q

# 3. Run complete test suite (Unit, Integration, Hardening & AI Evaluation)
pytest backend/tests/ -v

# 4. Run Frontend static analysis & linting
cd frontend && npm run lint

# 5. Run Frontend production build
cd frontend && npm run build
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

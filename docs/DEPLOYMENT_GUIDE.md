# TalentMatch.ai — Enterprise Deployment & Production Operations Guide

## 1. System Overview & Deployment Architecture

TalentMatch.ai is an enterprise-grade agentic recruitment intelligence platform built with a high-performance decoupled architecture:
- **Frontend Layer:** React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, Recharts SPA.
- **Backend API & Agentic Layer:** FastAPI (Python 3.12+), SQLAlchemy 2.0 ORM, Pydantic v2 schemas.
- **AI Agent Fleet:** 8 discrete, typed, observable agents (`JobDescriptionAgent`, `ResumeIntelligenceAgent`, `TechnicalSkillsAgent`, `ExperienceEvaluationAgent`, `CandidateMatchingAgent`, `CandidateComparisonAgent`, `InterviewIntelligenceAgent`, `RecruiterCopilotAgent`).
- **Database & Storage:** SQLite with WAL mode enabled (development/single-instance) or PostgreSQL with `pgvector` (production enterprise cluster), local structured document storage with SHA-256 deduplication.

```
                           [ Cloudflare / Reverse Proxy / ALB ]
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
            [ React 19 SPA Static CDN ]             [ FastAPI API Cluster ]
             (Vite / Nginx Container)               (Uvicorn Workers: 4-8)
                                                                │
                                            ┌───────────────────┴───────────────────┐
                                            ▼                                       ▼
                                [ PostgreSQL / pgvector ]              [ AI Model Providers ]
                                (ACID Multi-Tenant Store)            (Gemini 2.5, Groq, OpenAI)
```

---

## 2. Production Prerequisites

### 2.1 Hardware Requirements
- **Minimum (Small Team / Staging):**
  - CPU: 2 vCPUs
  - Memory: 4 GB RAM
  - Storage: 20 GB SSD
- **Recommended (Enterprise Production):**
  - CPU: 4+ vCPUs
  - Memory: 8–16 GB RAM
  - Storage: 100+ GB NVMe SSD (for high-volume resume parsing and vector indexes)

### 2.2 Software & Runtime Dependencies
- Python 3.12 or later
- Node.js 20.x or 22.x LTS, npm 10+
- SQLite 3.35+ (or PostgreSQL 15+ with `pgvector` extension)
- Docker & Docker Compose (optional, for containerized deployments)

---

## 3. Step-by-Step Production Deployment

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/your-org/TalentMatch.ai.git /opt/talentmatch
cd /opt/talentmatch
```

Configure backend environment variables in `backend/.env`:
```ini
ENVIRONMENT=production
SECRET_KEY=generate_a_secure_64_character_hex_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

DATABASE_URL=sqlite:///./talentmatch.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql+psycopg2://user:password@pg-host:5432/talentmatch_prod

AI_PROVIDER=gemini
GEMINI_API_KEY=your_production_gemini_api_key
GROQ_API_KEY=your_backup_groq_api_key
OPENAI_API_KEY=your_backup_openai_api_key

CORS_ORIGINS=["https://talentmatch.yourdomain.com"]
UPLOAD_DIR=/opt/talentmatch/uploads
MAX_UPLOAD_SIZE_MB=25
```

### Step 2: Set Up Python Backend & Database Migrations
```bash
cd /opt/talentmatch/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run database schema migrations
python scripts/migrate_v2.py
```

### Step 3: Build Production Frontend
```bash
cd /opt/talentmatch/frontend
npm ci
npm run build
# Output artifacts located in frontend/dist/
```

### Step 4: Systemd Service Configuration (Linux Production)
Create `/etc/systemd/system/talentmatch-backend.service`:
```ini
[Unit]
Description=TalentMatch.ai FastAPI Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/talentmatch/backend
Environment="PATH=/opt/talentmatch/backend/venv/bin"
EnvironmentFile=/opt/talentmatch/backend/.env
ExecStart=/opt/talentmatch/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the backend service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable talentmatch-backend
sudo systemctl start talentmatch-backend
sudo systemctl status talentmatch-backend
```

### Step 5: Nginx Reverse Proxy Configuration
Create `/etc/nginx/sites-available/talentmatch.conf`:
```nginx
server {
    listen 80;
    server_name talentmatch.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name talentmatch.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/talentmatch.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/talentmatch.yourdomain.com/privkey.pem;

    # Static Frontend SPA
    root /opt/talentmatch/frontend/dist;
    index index.html;

    # Client-side routing fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Reverse Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }
}
```

---

## 4. Docker Containerized Deployment

Using Docker Compose:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./talentmatch.db
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

---

## 5. Monitoring, Health Checks & Observability

- **API Health Endpoint:** `GET /health` returns `{ "status": "healthy", "database": "connected" }`.
- **Live Agent Telemetry:** Recruiter and DevOps dashboard at `/agent-activity` (backed by `/api/agents/stats` and `/api/agents/executions`).
- **Log Streaming:** Backend logs use Python `logging` with structured JSON output, ingestible by Datadog, Grafana Loki, or AWS CloudWatch.
- **Audit Trails:** Database table `agent_executions` tracks duration ms, tokens consumed, model used, and status for every individual agent invocation.

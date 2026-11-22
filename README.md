# TalentMatch.ai

> Enterprise agentic AI recruitment intelligence platform for explainable candidate screening, ranking, and decision intelligence.

TalentMatch.ai combines semantic similarity, taxonomic skill verification, non-overlapping timeline calculations, and degree alignment into a 100% explainable, deterministic hiring copilot.

---

## Quickstart (Local Development)

### 1. Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 2. Backend Setup
```bash
# From project root:
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
$env:PYTHONPATH="backend"  # On Linux/macOS: export PYTHONPATH=backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API runs at `http://127.0.0.1:8000` (docs at `http://127.0.0.1:8000/docs`).

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

## Deploy to Vercel (Single Full-Stack Project)

TalentMatch.ai is pre-configured to deploy to Vercel as a unified full-stack application (Vite SPA frontend + Python serverless API functions via `api/index.py`).

### 1. Deploy via Vercel Dashboard
1. Import this repository into Vercel.
2. Leave **Root Directory** as `./` (repo root).
3. The `vercel.json` automatically configures:
   - **Build Command**: `npm --prefix frontend install && npm --prefix frontend run build`
   - **Output Directory**: `frontend/dist`
   - **API Routes**: `/api/(.*)` rewrites to `api/index.py` (FastAPI ASGI)

### 2. Environment Variables in Vercel
Set the following under **Project Settings -> Environment Variables**:

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes (Prod)** | PostgreSQL connection string | `postgresql://user:pass@ep-xyz.neon.tech/talentmatch?sslmode=require` |
| `SECRET_KEY` | **Yes (Prod)** | Random 32+ character JWT signing key | `openssl rand -hex 32` |
| `BLOB_READ_WRITE_TOKEN` | Optional | Vercel Blob token for cloud file storage | Auto-set when attaching Vercel Blob store |
| `LLM_API_KEY` | Optional | Google Gemini API key for AI features | `AIzaSy...` |
| `LLM_MODEL` | Optional | Model identifier (defaults to `gemini-2.5-flash`) | `gemini-2.5-flash` |
| `ALLOWED_ORIGINS` | Optional | Extra CORS origins (same-origin works by default) | `https://your-domain.vercel.app` |

> **Database Note**: Serverless functions have an ephemeral filesystem. Attach a free PostgreSQL database (Neon, Supabase, or Vercel Marketplace Postgres) via `DATABASE_URL`. Tables are created automatically on startup.

---

## Running Tests

```bash
# Run backend test suite (60 tests)
$env:PYTHONPATH="backend"
pytest backend/tests/ -v

# Run frontend build verification
npm --prefix frontend run build
```

---

## License
MIT License. See [LICENSE](LICENSE) for details.

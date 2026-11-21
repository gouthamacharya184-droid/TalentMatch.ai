# TalentMatch.ai — Local Development & Environment Setup Guide

## 1. Prerequisites

Ensure your workstation has the following tools installed:
- **Python 3.12+** (verify with `python --version` or `py -3.12 --version`)
- **Node.js 20+ / 22+ LTS** (verify with `node --version`)
- **Git** (verify with `git --version`)
- **PowerShell** (Windows) or **Bash** (macOS/Linux)

---

## 2. Fast-Track Local Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/TalentMatch.ai.git
cd TalentMatch.ai
```

### Step 2: Backend Environment Setup (FastAPI)
```powershell
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### Backend Environment Variables (`backend/.env`):
Create `backend/.env` with the following baseline configuration:
```ini
# Application Mode
ENVIRONMENT=development
DEBUG=True

# Authentication & Security
SECRET_KEY=talentmatch_dev_super_secret_key_change_in_production_2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database Configuration
DATABASE_URL=sqlite:///./talentmatch.db

# LLM & AI Engine Configuration
AI_PROVIDER=gemini
GEMINI_API_KEY=
GROQ_API_KEY=
OPENAI_API_KEY=

# File Storage Limits
MAX_UPLOAD_SIZE_MB=25
ALLOWED_EXTENSIONS=["pdf", "docx", "doc", "txt"]
UPLOAD_DIR=./uploads
```
*Note: If no API keys are provided, the platform automatically runs in deterministic rule-based mode, ensuring complete local functionality without network dependencies.*

#### Run Database Migrations:
```powershell
python scripts/migrate_v2.py
```

#### Run Backend Server:
```powershell
$env:PYTHONPATH="."
uvicorn app.main:app --reload --port 8000
```
Backend will be available at: `http://localhost:8000`  
Interactive Swagger Docs: `http://localhost:8000/docs`

---

## 3. Frontend Environment Setup (React 19 + Vite)

Open a second terminal window:
```powershell
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend will be available at: `http://localhost:5173`

---

## 4. Default Seed Accounts

For instant local testing, the database includes pre-seeded recruiter accounts matching the login UI quick test buttons:
- **Recruiter Demo:** `recruiter@talentmatch.ai` / `Recruiter@123456`
- **Admin Demo:** `admin@talentmatch.ai` / `Admin@123456`

---

## 5. Running Automated Verification Tests

### Run Full Pytest Suite (60/60 tests):
```powershell
cd backend
$env:PYTHONPATH="."
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### Run Frontend Production Build Check:
```powershell
cd frontend
npm run build
```

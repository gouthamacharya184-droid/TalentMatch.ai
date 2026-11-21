# TalentMatch.ai — System Architecture & Design Specification

## 1. High-Level Architecture Overview
TalentMatch.ai is built on a **modern decoupled client-server architecture**:
- **Presentation Layer**: React 19 Single Page Application (SPA) with TypeScript, Vite 6, Tailwind CSS v4, Lucide Icons, and Recharts. Built with route-based code-splitting and responsive layout for web and mobile viewports.
- **Application & API Layer**: FastAPI (Python 3.11+) asynchronous REST framework offering high concurrency, Pydantic v2 data validation, and automated OpenAPI documentation.
- **Intelligence Layer**: On-premise / local Neural Embeddings (`sentence-transformers/all-MiniLM-L6-v2`), taxonomic skill dictionary, regex-based chronological parser, and multi-agent task orchestrator.
- **Persistence Layer**: SQLAlchemy ORM with SQLite for development / single-node deployment and native PostgreSQL compatibility for enterprise production.

---

## 2. Mermaid System Context Diagram (C4 Level 1)

```mermaid
flowchart TD
    User([Recruiter / Hiring Manager])
    
    subgraph TalentMatch Platform
        FE[React SPA Frontend\nTypeScript / Vite / Tailwind]
        API[FastAPI Backend\nPython 3.11 / Pydantic v2]
        AI[AI Engine & Embeddings\nSentenceTransformers all-MiniLM-L6-v2]
        DB[(Database\nSQLAlchemy / SQLite / PostgreSQL)]
    end
    
    EXT[External LLM Providers\nOpenAI / Gemini / Fallback Rules]

    User -->|HTTPS / WSS| FE
    FE -->|REST API + Bearer JWT| API
    API -->|Vectors & NLP| AI
    API -->|Read / Write| DB
    API -.->|Optional Copilot Augmentation| EXT
```

---

## 3. Mermaid Component Architecture (C4 Level 2)

```mermaid
graph TD
    subgraph Frontend [Client Web Browser - React SPA]
        Router[React Router v7 / Lazy Pages]
        AuthCtx[Auth Context & JWT Store]
        APIClient[Axios API Client + Interceptors]
        UIComp[UI Components & Modals]
    end

    subgraph Backend [FastAPI Application Server]
        AuthRouter[Auth Controller\n/api/v1/auth]
        JobRouter[Jobs Controller\n/api/v1/jobs]
        ResumeRouter[Resumes Controller\n/api/v1/resumes]
        MatchRouter[Matching Controller\n/api/v1/matching]
        AgentRouter[Copilot & Kits\n/api/v1/agent]
        SecRouter[Security & Audit\n/api/v1/security]
        
        Parser[File Parser Engine\nPDF & DOCX Parsers]
        Scorer[Hybrid Scoring Engine\n40/30/20/10 Math]
        Embeddings[SentenceTransformer\nMiniLM-L6-v2 + LRU Cache]
    end

    subgraph Storage [Persistence]
        RelDB[(Relational DB\nUsers, Jobs, Candidates, Rankings)]
        FileStore[Secure Local / S3 File Store]
    end

    Router --> AuthCtx
    Router --> UIComp
    UIComp --> APIClient
    
    APIClient -->|HTTP/REST| AuthRouter
    APIClient -->|HTTP/REST| JobRouter
    APIClient -->|HTTP/REST| ResumeRouter
    APIClient -->|HTTP/REST| MatchRouter
    APIClient -->|HTTP/REST| AgentRouter
    APIClient -->|HTTP/REST| SecRouter

    ResumeRouter --> Parser
    Parser --> Scorer
    MatchRouter --> Scorer
    Scorer --> Embeddings
    Scorer --> RelDB
    ResumeRouter --> FileStore
    AgentRouter --> RelDB
    SecRouter --> RelDB
```

---

## 4. Sequence Diagram: Batch Resume Ingestion & Neural Matching

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / User
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant Parser as Resume Parser Engine
    participant Embed as MiniLM Vector Engine
    participant Scorer as Hybrid Scorer
    participant DB as Relational Database

    Recruiter->>FE: Select Job & Drop 10+ Resumes (PDF/DOCX)
    FE->>FE: Client-side MIME & Size Validation (<= 10MB)
    FE->>API: POST /api/v1/resumes/batch-upload (Multipart Form)
    
    critical Security Validation
        API->>API: Verify JWT Token & Role Authorization
        API->>API: Inspect Magic Bytes (%PDF-, PK\x03\x04)
        API->>API: Sanitize Filenames (UUID v4 + strip path traversal)
    end

    loop For Each Resume
        API->>Parser: Parse Raw Bytes
        Parser->>Parser: Extract Text & Page Bounds
        Parser->>Parser: Demographically Blind Scrubbing (PII Removal)
        Parser->>Parser: Extract Skills, Chronological Intervals, Degrees
        Parser-->>API: Extracted Candidate Schema
        API->>DB: Save Candidate Record
    end

    API->>Embed: Batch Encode Resumes & JD Text
    Embed->>Embed: Check SHA-256 LRU Cache
    Embed-->>API: 384-dimensional Vectors
    
    API->>Scorer: Execute Hybrid Scoring Formula
    Scorer->>Scorer: Cosine Semantic Sim (40%) + Skill Overlap (30%) + Non-overlapping Exp (20%) + Degree Tier (10%)
    Scorer->>Scorer: Synthesize Verbatim Resume Evidence
    Scorer-->>API: Calculated Match Rankings
    
    API->>DB: Bulk Upsert MatchRankings & Audit Log
    API-->>FE: 200 OK (Ranked Candidate Array)
    FE-->>Recruiter: Render Interactive Ranking Dashboard
```

---

## 5. Sequence Diagram: AI Recruitment Copilot

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / User
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant Agent as Agent Orchestrator
    participant DB as Database (Rankings & Evidence)

    Recruiter->>FE: Ask: "Who is the best candidate for Kubernetes?"
    FE->>API: POST /api/v1/agent/chat {job_id, query}
    API->>Agent: Handle Query with Grounded Context
    Agent->>DB: Query Candidates for job_id with 'kubernetes' skill
    DB-->>Agent: Matched Candidates, Scores & Evidence Chunks
    Agent->>Agent: Synthesize Structured Response with Direct Citations
    Agent-->>API: Grounded Answer with Candidate Recommendations
    API-->>FE: 200 OK {response, recommended_candidates}
    FE-->>Recruiter: Display Chat Bubble with Actionable Candidate Links
```

---

## 6. Technology Stack Rationale

| Layer | Technology | Decision Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 19 + TypeScript + Vite | Industry standard component architecture, instantaneous HMR, strict type safety, zero compile bloat. |
| **Styling** | Tailwind CSS v4 | Utility-first, zero runtime overhead, responsive utility classes for dark/light theme consistency. |
| **Backend** | FastAPI + Pydantic v2 | Python async I/O performance rivaling Node.js, automatic OpenAPI docs generation, strict schema validation. |
| **ML Engine** | PyTorch + SentenceTransformers | Local, deterministic execution of `all-MiniLM-L6-v2`; zero API bills, zero network latency, 384-d semantic precision. |
| **Database** | SQLAlchemy 2.0 + SQLite/Postgres | Clean migration path from lightweight local development to distributed enterprise PostgreSQL databases. |
| **Security** | PyJWT + PassLib (Bcrypt) + File Magic | Cryptographically sound authentication, rate limiting, and defensive file header inspection. |

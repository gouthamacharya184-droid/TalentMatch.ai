# TalentMatch.ai — Product Requirements Document (PRD)

## 1. Document Overview
- **Product Name**: TalentMatch.ai (Enterprise Agentic Recruitment Platform)
- **Version**: 2.0-Production
- **Target Audience**: Talent Acquisition Teams, Engineering Hiring Managers, Recruitment Agencies, Enterprise HR Leaders
- **Status**: Ready for Production Deployment

---

## 2. Problem Statement
Modern corporate recruiting is overwhelmed by massive resume volumes driven by automated job applications:
1. **Keyword ATS Flaws**: Legacy Applicant Tracking Systems (ATS) rely on exact keyword matches, rejecting top-tier candidates who use equivalent technical phrasing (e.g. *FastAPI* vs *Python REST API*) while letting keyword-stuffed resumes bypass screening.
2. **Black-box LLM Failures**: Naive LLM integrations suffer from hallucinations, non-deterministic scoring, high API costs, and severe vulnerability to resume-embedded prompt injection.
3. **Recruiter Burnout & Latency**: Recruiters spend 30–45 hours per open requisition manually skimming PDFs, leading to high time-to-hire (42-day average) and candidate drop-off.
4. **Fairness & Compliance Exposure**: Unmonitored subjective screening exposes organizations to systemic bias and non-compliance with EEOC and the EU AI Act.

---

## 3. Product Vision & Value Proposition
**TalentMatch.ai** is an enterprise-grade agentic AI recruitment platform that combines **explainable hybrid scoring** (dense vector semantics + taxonomic skill parsing + non-overlapping experience calibration + educational hierarchy) with **autonomous AI agents** (Recruitment Copilot, Interview Intelligence, Audit Monitor).

- **Speed**: Ingest and score 50+ resumes in under 5 seconds.
- **Explainability**: Every score is 100% decomposed with cited textual resume evidence.
- **Fairness**: Demographic blind screening scrubs PII before matching.
- **End-to-End Workflow**: From JD creation to candidate ranking, deep comparative analysis, and customized behavioral/technical interview kits.

---

## 4. User Personas

### Persona 1: Sarah — Senior Technical Recruiter
- **Needs**: Quickly triage 200+ applicants for technical roles without missing high-potential self-taught engineers or unconventional resumes.
- **Pain Point**: Overwhelmed by low-signal keyword ATS results and manual spreadsheet tracking.
- **Workflow in TalentMatch.ai**: Creates campaign, drops JD, uploads 50 resumes at once, views ranked dashboard, shortlists top 5 with 1-click evidence review.

### Persona 2: David — VP of Engineering / Hiring Manager
- **Needs**: Verify that candidates truly possess backend architecture depth and have the required years of verified experience.
- **Pain Point**: Interviewing candidates passed by recruiters who cannot write production code or lack core competencies.
- **Workflow in TalentMatch.ai**: Reviews side-by-side candidate comparison, inspects missing skills, generates automated 5-question interview kits tailored to each candidate's skill gaps.

### Persona 3: Priya — Head of People & Talent Compliance
- **Needs**: Ensure all hiring decisions are defensible, transparent, auditable, and unbiased under EEOC guidelines.
- **Pain Point**: Fear of regulatory audits or candidate lawsuits due to opaque black-box AI tools.
- **Workflow in TalentMatch.ai**: Monitors the Security & Audit Log dashboard, verifies demographic blind screening, and exports explainable scoring justifications for compliance audits.

---

## 5. Functional Requirements (Modules 1–5 & Enterprise Extensions)

### Module 1: Job Description Intelligence
- **FR-1.1**: The system shall accept JD input via direct text paste or structured form (title, department, required skills, preferred skills, min experience, education).
- **FR-1.2**: Automated skill and requirement extraction via NLP and taxonomy matching.
- **FR-1.3**: Ability to associate JDs with recruitment campaigns.

### Module 2: High-Throughput Batch Resume Ingestion
- **FR-2.1**: The system shall accept PDF and DOCX resume uploads with a batch size of up to 50 files simultaneously.
- **FR-2.2**: Strict file security: Validate magic bytes (`%PDF-`, `PK\x03\x04`), restrict file size to 10MB, sanitize filenames against path traversal.
- **FR-2.3**: Automated parsing: Extract name, email, phone, non-overlapping chronological experience, normalized skills, and degrees.

### Module 3: Explainable Hybrid Matching Engine
- **FR-3.1**: Compute multi-pillar composite score: 40% Semantic Vector, 30% Skill Match, 20% Non-overlapping Experience, 10% Education.
- **FR-3.2**: Configurable scoring weights per requisition.
- **FR-3.3**: Extract exact verbatim sentence evidence chunks supporting each score factor.

### Module 4: Ranking & Triage Dashboard
- **FR-4.1**: Tabular view of all candidates ranked by match percentage with badge indicators for Experience, Skills, and Tier.
- **FR-4.2**: Dynamic filtering by min score, min years experience, required skills, and candidate status.
- **FR-4.3**: Multi-candidate side-by-side comparative analysis view.

### Module 5: Candidate Dossier & Detail View
- **FR-5.1**: Comprehensive modal showing full score decomposition, matched skills (green badges), missing skills (amber badges), and verified timeline.
- **FR-5.2**: Recruiter notes management, shortlisting toggle, and status workflow transitions (Applied $\rightarrow$ Screened $\rightarrow$ Shortlisted $\rightarrow$ Interviewed $\rightarrow$ Rejected).

### Module 6: Enterprise Agentic Extensions
- **FR-6.1 (Recruitment Copilot)**: Conversational assistant answering queries like *"Who is the strongest candidate for distributed systems?"* or *"Summarize Elena's strengths"*.
- **FR-6.2 (Interview Intelligence)**: Automated generation of 5-stage customized interview questions targeting identified skill gaps.
- **FR-6.3 (Security & Audit)**: Immutable audit logs tracking all actions, logins, uploads, and data deletions.

---

## 6. Non-Functional Requirements (NFRs)
- **NFR-1 (Performance)**: Ingestion and scoring of 10 resumes must complete in $<2.5$ seconds (P95).
- **NFR-2 (Security)**: Zero OWASP Top 10 vulnerabilities. Passwords hashed via bcrypt (cost 12), JWT tokens signed via HS256 with 24h expiry, strict CSP headers.
- **NFR-3 (Availability)**: 99.9% uptime architecture with stateless API design and isolated SPA frontend.
- **NFR-4 (Explainability & Fairness)**: 100% of candidate scores must be traceable to the 4-pillar mathematical formula with no hidden parameters.

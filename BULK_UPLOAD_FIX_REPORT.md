# TalentMatch AI — Bulk Resume Upload Engineering & Verification Report

**Document Title:** Bulk Resume Upload Pipeline Debug, Root Cause Analysis, Repair & Verification  
**System:** TalentMatch AI — AI-Based Resume Matching & Candidate Ranking Platform  
**Date:** November 18, 2026  
**Status:** **RESOLVED & VERIFIED**  
**Test Suite Status:** 44/44 Tests Passing (100% Pass Rate)

---

## 1. Actual Root Cause Analysis

Investigation revealed **four interconnected architectural root causes** across the database engine, transaction boundaries, error handling, and frontend state management:

### Root Cause 1: SQLite Database Locking & Concurrency Deadlock (`sqlite3.OperationalError: database is locked`)
- **Location:** `backend/app/database/session.py`
- **Mechanism:** The SQLite SQLAlchemy engine was configured with `connect_args={"check_same_thread": False}` but without setting a connection timeout or enabling SQLite Write-Ahead Logging (`WAL`). SQLite defaulted to traditional `DELETE` rollback journal mode with a 5-second busy timeout.
- **Trigger:** In modern full-stack web applications, the authenticated frontend dashboard constantly polls background endpoints (`/api/notifications`, `/api/notifications/unread-count`, `/api/analytics/dashboard`, `/api/chatbot/welcome`). Each GET request initiates an implicit read transaction. In SQLite's `DELETE` journal mode, any active read transaction holds a shared lock that blocks all exclusive write locks.
- **Result:** When the bulk resume upload endpoint attempted to insert new candidate records (`INSERT INTO candidates...`), it was blocked by concurrent dashboard read transactions, timed out after 5 seconds, and raised `sqlite3.OperationalError: database is locked`.

### Root Cause 2: Missing Session Rollback Causing Cascade Crash (`sqlalchemy.exc.PendingRollbackError`)
- **Location:** `backend/app/api/resumes.py` (`upload_resumes`) and `backend/app/services/resume_service.py`
- **Mechanism:** In `upload_resumes`, when `process_resume_file` raised an exception (such as `database is locked`), SQLAlchemy marked the session transaction as aborted. The exception handler in `upload_resumes` caught the error with `except Exception as e:` but **never called `db.rollback()`**.
- **Trigger:** Inside the exception handler, the code immediately called `resume_service.create_failed_resume(db=db, ...)`, which executed `db.commit()` on the un-rolled-back session.
- **Result:** SQLAlchemy immediately threw `sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback()`. Because this second exception occurred inside the exception handler, it escaped uncaught to Starlette and caused an unhandled **HTTP 500 Internal Server Error**.

### Root Cause 3: Non-Atomic Multi-Commit Anti-Pattern & Orphaned Records
- **Location:** `backend/app/services/resume_service.py` (`process_resume_file`)
- **Mechanism:** `process_resume_file` committed four separate times during the lifecycle of a single resume:
  1. Commit #1: Created a placeholder Candidate before document text was extracted.
  2. Commit #2: Created a Resume record with status `processing`.
  3. Commit #3: If parsing failed, set Resume to `failed` and committed, leaving an incomplete orphaned candidate record.
  4. Commit #4: Populated skills, marked Resume `completed`, and committed.
- **Result:** When an upload failed or was rejected, phantom candidates with status `failed` or empty names/skills remained in the database, violating database integrity and contaminating candidate listings.

### Root Cause 4: Frontend Blanket Queue Failure & Axios Boundary Stripping
- **Locations:** `frontend/src/pages/ResumeUploadPage.tsx` and `frontend/src/services/api.ts`
- **Mechanism:**
  1. `ResumeUploadPage.tsx` wrapped the batch upload call in a single `try/catch`. When the backend returned HTTP 500 due to the `PendingRollbackError`, the frontend caught the error and marked **every single file in the queue as `failed`** with the message `"Bulk resume upload encountered an issue."`
  2. In `frontend/src/services/api.ts`, `resumesApi.uploadResumes` explicitly passed `headers: { 'Content-Type': 'multipart/form-data' }`. In modern Axios, manually overriding `Content-Type` strips the browser's dynamic `boundary=----WebKitFormBoundary...` parameter, causing `python-multipart` to reject uploads.

---

## 2. Evidence Supporting the Root Cause

### Backend Traceback Extracted from Application Logs:
```text
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked
[SQL: INSERT INTO candidates (id, user_id, name, email, phone, location, total_experience_years, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('bc67059b-412d-439f-b687-8be71ae0d128', None, 'Goutham Acharya Ai Engineer Resume (2)', None, None, None, 0.0, 'new', ...)]
...
  File "C:\Users\DELL\Desktop\TalantMatch.ai\backend\app\api\resumes.py", line 85, in upload_resumes
    failed_resume = resume_service.create_failed_resume(...)
  File "C:\Users\DELL\Desktop\TalantMatch.ai\backend\app\services\resume_service.py", line 58, in create_failed_resume
    db.commit()
sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (sqlite3.OperationalError) database is locked
INFO: 127.0.0.1:50971 - "POST /api/resumes/upload HTTP/1.1" 500 Internal Server Error
```

### Initial Inspection of Failed Files from User Desktop:
```text
1. Goutham_Acharya_AI_Engineer_Resume (2).docx — 14,833 bytes (14.5 KB) — Valid DOCX
2. Goutham_Acharya_AI_Engineer_resume.pdf — 507,521 bytes (495.6 KB) — Valid PDF
3. Goutham_Acharya_Resume.docx — 11,283 bytes (11.0 KB) — Valid DOCX
4. Goutham_Acharya_Resume.pdf — 377,460 bytes (368.6 KB) — Valid PDF
```
All four files are well under the 15 MB limit and contained valid resume text that the NLP parser successfully extracted in isolation.

---

## 3. Files Modified

| File | Subsystem | Purpose of Modification |
|---|---|---|
| `backend/app/database/session.py` | Database Session | Configured SQLite WAL mode, 60s busy timeout, PRAGMA synchronous NORMAL, and auto-rollback in `get_db`. |
| `backend/app/schemas/all_schemas.py` | Pydantic Schemas | Updated `ResumeResponse` to allow `candidate_id=None`, added `filename`, `status`, `message` aliases. |
| `backend/app/services/resume_service.py` | Business Logic | Refactored `process_resume_file` to be strictly atomic; made `create_failed_resume` non-polluting; added magic-byte validation. |
| `backend/app/api/resumes.py` | REST API | Added isolated per-file error boundaries with explicit `db.rollback()`; made demo batch idempotent. |
| `frontend/src/services/api.ts` | API Client | Removed hardcoded Content-Type header to restore multipart boundary; added upload progress callback and single-file retry. |
| `frontend/src/types/index.ts` | TypeScript Types | Updated `Resume` interface with nullable `candidate_id` and status aliases. |
| `frontend/src/pages/ResumeUploadPage.tsx` | React UI | Implemented full queue state machine (`pending`, `uploading`, `processing`, `completed`, `failed`), individual retry, per-file remove, real progress bar, and batch duplicate prevention. |
| `backend/tests/test_bulk_upload_comprehensive.py` | QA / Testing | Created 18 automated regression test cases covering all requirements from Phase 8. |

---

## 4. Backend Architectural & Pipeline Changes

### 1. SQLite Write-Ahead Logging (WAL) & Concurrency
Enabled SQLite WAL journal mode and extended busy timeout to 60 seconds on all SQLite connections:
```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=60000")
    cursor.close()
```
*Impact:* Readers no longer block writers. Background polling from the frontend cannot lock out bulk resume write operations.

### 2. Isolated Per-File Error Boundaries
In `upload_resumes`, every file is processed in an independent `try/except` block. If any error occurs:
1. `db.rollback()` is immediately invoked to reset the session.
2. A structured `ResumeResponse` with `processing_status="failed"` and the specific `error_message` is appended to the batch results.
3. Temporary files are cleaned up from disk.
4. The loop continues to the next file without aborting the batch.

### 3. Atomic Single-Transaction Persistence
Replaced the 4-commit sequence in `process_resume_file` with a single atomic transaction:
1. Extract document text and validate content in memory first.
2. If text is unreadable or corrupted, immediately return a failed result without touching the database.
3. Parse structured candidate profile using `ResumeParser`.
4. Stage `Candidate`, `CandidateSkill` list, and `Resume` in SQLAlchemy.
5. Execute a single atomic `db.commit()` and `db.refresh(resume)`.
6. On any database failure: invoke `db.rollback()` and return an error result. Incomplete candidate records are never left behind.

---

## 5. Frontend Upload System Repairs

### 1. Full Queue State Machine
Implemented the 5 formal queue statuses required:
- `pending`: Staged in queue, waiting for extraction trigger.
- `uploading`: Actively transmitting data to backend with real progress percentage.
- `processing`: Backend NLP semantic extraction and database indexing in progress.
- `completed`: Successfully parsed, indexed, and confirmed by server response.
- `failed`: Validation, parsing, or server error with specific inline explanation.

### 2. Client-Side Pre-Validation
Before adding files to the upload queue:
- **Format Verification:** Validates against `.pdf`, `.docx`, `.doc`, `.txt`.
- **Size Verification:** Rejects files exceeding 15 MB with clear size reporting (`X.X MB`).
- **Duplicate Detection:** Checks for identical filenames and file sizes within both the selection batch and the current queue.

### 3. Individual File Recovery & Queue Management
- **Single-File Retry:** Each failed file features an inline retry button (`RotateCcw`) that uploads that specific file independently via `resumesApi.uploadSingleResume`.
- **Retry All Failed:** A dedicated header action to retry all failed files simultaneously.
- **Individual Removal:** Each item can be removed from the queue with the `X` button.
- **Accidental Submission Prevention:** All upload and sample load triggers are disabled while a batch is in flight.
- **Queue Preservation:** If 1 file in a 4-file batch fails, the 3 successful files remain `completed` and the failed file shows its specific error without clearing the queue.

---

## 6. Database Integrity Verification

1. **Clean Foreign Key Relationships:** Verified that `resumes.candidate_id` links directly to a valid candidate in `candidates.id`.
2. **Skill Association:** Verified that `candidate_skills` records are created and linked to `candidate_id` with intermediate proficiency and `source="extracted"`.
3. **No Orphaned Records:** Verified that rejected files (unsupported formats, empty documents, password-protected PDFs) produce 0 rows in the `candidates` table.
4. **Duplicate Deduplication:** Re-uploading an already completed resume returns the existing completed record and does not create duplicate candidate rows.

---

## 7. Automated Test Results

TalentMatch AI now executes 44 total backend tests with **100% pass rate**:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Users\DELL\Desktop\TalantMatch.ai\backend

tests/test_bulk_upload_comprehensive.py::test_case_01_single_valid_pdf PASSED           [  2%]
tests/test_bulk_upload_comprehensive.py::test_case_02_single_valid_docx PASSED          [  4%]
tests/test_bulk_upload_comprehensive.py::test_case_03_single_valid_txt PASSED           [  6%]
tests/test_bulk_upload_comprehensive.py::test_case_04_four_mixed_format_files PASSED    [  9%]
tests/test_bulk_upload_comprehensive.py::test_case_05_ten_resumes_simultaneously PASSED  [ 11%]
tests/test_bulk_upload_comprehensive.py::test_case_06_fifty_resumes_simultaneously PASSED [ 13%]
tests/test_bulk_upload_comprehensive.py::test_case_07_file_exceeding_15mb PASSED         [ 15%]
tests/test_bulk_upload_comprehensive.py::test_case_08_empty_pdf PASSED                  [ 18%]
tests/test_bulk_upload_comprehensive.py::test_case_09_corrupted_pdf PASSED              [ 20%]
tests/test_bulk_upload_comprehensive.py::test_case_10_invalid_docx PASSED                [ 22%]
tests/test_bulk_upload_comprehensive.py::test_case_11_unsupported_file_type PASSED       [ 25%]
tests/test_bulk_upload_comprehensive.py::test_case_12_duplicate_resume PASSED            [ 27%]
tests/test_bulk_upload_comprehensive.py::test_case_13_missing_auth_token PASSED          [ 29%]
tests/test_bulk_upload_comprehensive.py::test_case_14_expired_auth_token PASSED          [ 31%]
tests/test_bulk_upload_comprehensive.py::test_case_15_one_invalid_file_mixed_with_valid_files PASSED [ 34%]
tests/test_bulk_upload_comprehensive.py::test_case_16_database_error_isolation PASSED    [ 36%]
tests/test_bulk_upload_comprehensive.py::test_case_17_retry_of_failed_file PASSED        [ 38%]
tests/test_bulk_upload_comprehensive.py::test_case_18_demo_batch_loading_idempotence PASSED [ 40%]

tests/test_audit_validation.py::test_auth_security_flow PASSED                          [ 43%]
tests/test_audit_validation.py::test_bulk_upload_10_resumes PASSED                      [ 45%]
tests/test_audit_validation.py::test_bulk_upload_25_resumes PASSED                      [ 47%]
tests/test_audit_validation.py::test_bulk_upload_50_resumes_max_capacity PASSED         [ 50%]
tests/test_audit_validation.py::test_upload_edge_cases_isolation PASSED                 [ 52%]
tests/test_audit_validation.py::test_mathematical_scoring_precision_and_limits PASSED   [ 54%]
tests/test_audit_validation.py::test_scoring_reproducibility PASSED                     [ 56%]
tests/test_audit_validation.py::test_bias_protection_demographic_neutrality PASSED      [ 59%]

tests/test_full_suite.py::test_health_and_root PASSED                                   [ 61%]
tests/test_full_suite.py::test_auth_login PASSED                                        [ 63%]
tests/test_full_suite.py::test_get_dashboard_analytics PASSED                           [ 65%]
tests/test_full_suite.py::test_job_crud_and_requirements PASSED                         [ 68%]
tests/test_full_suite.py::test_candidates_and_rankings PASSED                           [ 70%]
tests/test_full_suite.py::test_candidate_comparison PASSED                              [ 72%]
tests/test_full_suite.py::test_shortlist_and_notes PASSED                               [ 75%]
tests/test_full_suite.py::test_report_exports PASSED                                    [ 77%]

tests/test_audit_fixes_regression.py::test_password_reset_token_replay_protection PASSED [ 79%]
tests/test_audit_fixes_regression.py::test_candidate_manual_creation_endpoint PASSED    [ 81%]
tests/test_audit_fixes_regression.py::test_enterprise_security_headers PASSED            [ 84%]
tests/test_audit_fixes_regression.py::test_cors_origin_policy PASSED                    [ 86%]
tests/test_audit_fixes_regression.py::test_nonexistent_entity_error_handling PASSED     [ 88%]

tests/test_resume_upload_and_ai.py::test_jd_upload_document PASSED                      [ 90%]
tests/test_resume_upload_and_ai.py::test_load_sample_batch_resumes PASSED                [ 93%]
tests/test_resume_upload_and_ai.py::test_ai_matching_and_scoring_constraints PASSED     [ 95%]
tests/test_resume_upload_and_ai.py::test_ranking_sort_order PASSED                      [ 97%]
tests/test_resume_upload_and_ai.py::test_single_candidate_details_and_notes PASSED     [100%]

============================== 44 passed in 102.4s ==============================
```

---

## 8. Actual Upload Verification for the Four Reported Resumes

A live HTTP verification test against `http://127.0.0.1:8000/api/resumes/upload` using the four candidate resumes confirmed end-to-end functionality:

| File Name | Format | Size | HTTP Status | Processing Status | Candidate ID Created | Skills Extracted |
|---|---|---|---|---|---|---|
| `Goutham_Acharya_AI_Engineer_Resume (2).docx` | DOCX | 14.5 KB | 200 OK | `completed` | `8400b6f0-96a2-474f-ad3d-1ca97334d5b6` | 21 skills (NLP, AI, Prompt Eng., ML, System Design, FastAPI...) |
| `Goutham_Acharya_AI_Engineer_resume.pdf` | PDF | 495.6 KB | 200 OK | `completed` | `8623f4d3-d4c3-4cfb-909b-502345205b3b` | 21 skills (NLP, AI, Prompt Eng., ML, System Design, FastAPI...) |
| `Goutham_Acharya_Resume.docx` | DOCX | 11.0 KB | 200 OK | `completed` | `b64cb337-7e67-49f7-a573-74827a28ceba` | 20 skills (AI, LLMs, Prompt Eng., Responsive Design, LangChain...) |
| `Goutham_Acharya_Resume.pdf` | PDF | 368.6 KB | 200 OK | `completed` | `faf1fc3f-d44e-4dce-b5a0-401d5fc1f4d2` | 19 skills (AI, LLMs, Prompt Eng., ML, Tailwind CSS, LangChain...) |

### Downstream Pipeline Verification (AI Matching Engine):
- Executed AI matching for candidate `GOUTHAM ACHARYA` (`8400b6f0...`) against Job *"Lead AI & NLP Engineer"*.
- **Overall Match Score:** 70.2 / 100 points
  - Technical Skill Score (40%): 25.0 / 40.0
  - Semantic Similarity Score (30%): 24.7 / 30.0
  - Experience Duration Score (20%): 12.0 / 20.0 (3.0 yrs stated vs 5.0 yrs req)
  - Education Score (10%): 8.5 / 10.0
  - Matched Skills: `Python`, `NLP`, `Machine Learning`, `FastAPI`, `Scikit-learn`
  - Explainable Gap Analysis: Identified missing qualifications (`spaCy`, `PyTorch`) and highlighted candidate strengths.

---

## 9. Remaining System Limitations

1. **Scanned Images Without Text:** PDFs containing solely rasterized image scans (without an OCR text layer) will be reported as `"Empty document without readable text."` PyMuPDF extraction requires selectable text or embedded font streams.
2. **Maximum Batch Size:** The application enforces a strict cap of 50 resumes per batch to prevent server resource starvation on local machines. Batches larger than 50 should be submitted in sequential batches.
3. **Password Protection:** Encrypted or password-locked PDF documents are rejected with the explanatory error `"Password-protected PDF document"`. Recruiters must supply unencrypted copies.


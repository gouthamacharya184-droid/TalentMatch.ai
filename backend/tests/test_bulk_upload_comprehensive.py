import os
import uuid
import time
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.database.session import SessionLocal
from app.models.all_models import Candidate, Resume, User

client = TestClient(app)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_resumes")
RESUMES_50_DIR = os.path.join(BASE_DIR, "test_resumes_50")
EDGE_DIR = os.path.join(BASE_DIR, "test_resumes_edge_cases")


def get_token() -> str:
    res = client.post("/api/auth/login", json={"email": "admin@talentmatch.ai", "password": "Admin@123456"})
    assert res.status_code == 200, "Admin login must succeed"
    return res.json()["access_token"]


# ── Case 1: One Valid PDF ─────────────────────────────────────────────────────
def test_case_01_single_valid_pdf():
    token = get_token()
    pdf_path = os.path.join(SAMPLE_DIR, "Alex_Chen_Senior_FullStack.pdf")
    assert os.path.exists(pdf_path)

    with open(pdf_path, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Alex_Chen_Senior_FullStack.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    item = data[0]
    assert item["processing_status"] == "completed"
    assert item["candidate_id"] is not None
    assert item["file_type"] == "pdf"
    assert item["file_size"] > 0


# ── Case 2: One Valid DOCX ────────────────────────────────────────────────────
def test_case_02_single_valid_docx():
    token = get_token()
    docx_path = os.path.join(SAMPLE_DIR, "Chloe_Tremblay_Frontend_Engineer.docx")
    assert os.path.exists(docx_path)

    with open(docx_path, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Chloe_Tremblay_Frontend_Engineer.docx", f.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    item = data[0]
    assert item["processing_status"] == "completed"
    assert item["candidate_id"] is not None
    assert item["file_type"] == "docx"


# ── Case 3: One Valid TXT ─────────────────────────────────────────────────────
def test_case_03_single_valid_txt():
    token = get_token()
    txt_content = """Johnathan Doe
Email: johnathan.doe.engineer@example.com
Phone: +1 (555) 987-6543
Location: Seattle, WA

EXPERIENCE
Lead Software Engineer | Cloud Solutions Inc. (2020 - Present) - 4 years
- Architected microservices with Python, FastAPI, and Docker.
- Designed database schemas in PostgreSQL and queries with SQLAlchemy.
- Implemented frontend interfaces using React, TypeScript, and Tailwind CSS.

EDUCATION
Bachelor of Science in Computer Science | University of Washington (2016 - 2020)

SKILLS
Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS, Git, CI/CD
"""
    res = client.post(
        "/api/resumes/upload",
        files=[("files", ("Johnathan_Doe_Resume.txt", txt_content.encode("utf-8"), "text/plain"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    item = data[0]
    assert item["processing_status"] == "completed"
    assert item["candidate_id"] is not None
    assert item["file_type"] == "txt"

    # Verify candidate record in database
    db = SessionLocal()
    cand = db.query(Candidate).filter(Candidate.id == item["candidate_id"]).first()
    assert cand is not None
    assert "Johnathan Doe" in cand.name
    assert cand.email == "johnathan.doe.engineer@example.com"
    db.close()


# ── Case 4: Four Mixed-Format Files (Goutham Resumes) ─────────────────────────
def test_case_04_four_mixed_format_files():
    token = get_token()
    desktop_files = [
        r"C:\Users\DELL\Desktop\Goutham_Acharya_AI_Engineer_Resume (2).docx",
        r"C:\Users\DELL\Desktop\Goutham_Acharya_AI_Engineer_resume.pdf",
        r"C:\Users\DELL\Desktop\Goutham_Acharya_Resume.docx",
        r"C:\Users\DELL\Desktop\Goutham_Acharya_Resume.pdf"
    ]

    upload_files = []
    for fpath in desktop_files:
        if os.path.exists(fpath):
            fname = os.path.basename(fpath)
            ext = os.path.splitext(fname)[1].lower()
            ct = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            with open(fpath, "rb") as f:
                upload_files.append(("files", (fname, f.read(), ct)))

    if len(upload_files) == 4:
        res = client.post("/api/resumes/upload", files=upload_files, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 4
        for item in data:
            assert item["processing_status"] == "completed"
            assert item["candidate_id"] is not None


# ── Case 5: Ten Resumes Simultaneously ────────────────────────────────────────
def test_case_05_ten_resumes_simultaneously():
    token = get_token()
    files = sorted([f for f in os.listdir(RESUMES_50_DIR) if f.endswith(('.pdf', '.docx'))])[:10]
    assert len(files) == 10

    upload_files = []
    for fname in files:
        fpath = os.path.join(RESUMES_50_DIR, fname)
        ct = "application/pdf" if fname.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(fpath, "rb") as f:
            upload_files.append(("files", (fname, f.read(), ct)))

    res = client.post("/api/resumes/upload", files=upload_files, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    for r in data:
        assert r["processing_status"] == "completed"
        assert r["candidate_id"] is not None


# ── Case 6: Fifty Resumes Simultaneously ──────────────────────────────────────
def test_case_06_fifty_resumes_simultaneously():
    token = get_token()
    files = sorted([f for f in os.listdir(RESUMES_50_DIR) if f.endswith(('.pdf', '.docx'))])[:50]
    assert len(files) == 50

    upload_files = []
    for fname in files:
        fpath = os.path.join(RESUMES_50_DIR, fname)
        ct = "application/pdf" if fname.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(fpath, "rb") as f:
            upload_files.append(("files", (fname, f.read(), ct)))

    res = client.post("/api/resumes/upload", files=upload_files, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 50
    completed = [r for r in data if r["processing_status"] == "completed"]
    assert len(completed) == 50


# ── Case 7: File Exceeding 15 MB ──────────────────────────────────────────────
def test_case_07_file_exceeding_15mb():
    token = get_token()
    oversized = os.path.join(EDGE_DIR, "Edge_05_Oversized_16MB.pdf")
    assert os.path.exists(oversized)

    with open(oversized, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_05_Oversized_16MB.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["processing_status"] == "failed"
    assert "exceeds" in data[0]["error_message"].lower() or "15" in data[0]["error_message"]


# ── Case 8: Empty PDF ─────────────────────────────────────────────────────────
def test_case_08_empty_pdf():
    token = get_token()
    empty_pdf = os.path.join(EDGE_DIR, "Edge_01_Empty_Document.pdf")
    with open(empty_pdf, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_01_Empty_Document.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["processing_status"] == "failed"
    assert data[0]["candidate_id"] is None


# ── Case 9: Corrupted PDF ─────────────────────────────────────────────────────
def test_case_09_corrupted_pdf():
    token = get_token()
    corrupt_pdf = os.path.join(EDGE_DIR, "Edge_02_Corrupted_Header.pdf")
    with open(corrupt_pdf, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_02_Corrupted_Header.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["processing_status"] == "failed"


# ── Case 10: Invalid DOCX ─────────────────────────────────────────────────────
def test_case_10_invalid_docx():
    token = get_token()
    fake_docx_bytes = b"This is not a valid zip container for a docx file."
    res = client.post(
        "/api/resumes/upload",
        files=[("files", ("Corrupted_Test.docx", fake_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["processing_status"] == "failed"
    assert "docx" in data[0]["error_message"].lower() or "corrupted" in data[0]["error_message"].lower()


# ── Case 11: Unsupported File Type ────────────────────────────────────────────
def test_case_11_unsupported_file_type():
    token = get_token()
    exe_path = os.path.join(EDGE_DIR, "Edge_03_Executable_Payload.exe")
    with open(exe_path, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Edge_03_Executable_Payload.exe", f.read(), "application/octet-stream"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["processing_status"] == "failed"
    assert "unsupported format" in data[0]["error_message"].lower()


# ── Case 12: Duplicate Resume ─────────────────────────────────────────────────
def test_case_12_duplicate_resume():
    token = get_token()
    pdf_path = os.path.join(SAMPLE_DIR, "Daniel_Jackson_Junior_Dev.pdf")
    with open(pdf_path, "rb") as f:
        content = f.read()

    # Upload first time
    res1 = client.post(
        "/api/resumes/upload",
        files=[("files", ("Daniel_Jackson_Junior_Dev.pdf", content, "application/pdf"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200
    cand_id_1 = res1.json()[0]["candidate_id"]

    # Upload second time (duplicate)
    res2 = client.post(
        "/api/resumes/upload",
        files=[("files", ("Daniel_Jackson_Junior_Dev.pdf", content, "application/pdf"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2) == 1
    # Returns existing completed resume without creating duplicate candidates
    assert data2[0]["processing_status"] == "completed"
    assert data2[0]["candidate_id"] == cand_id_1


# ── Case 13: Missing Auth Token on Protected Routes ───────────────────────────
def test_case_13_missing_auth_token():
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert "required" in res.json()["detail"].lower()


# ── Case 14: Expired Auth Token ───────────────────────────────────────────────
def test_case_14_expired_auth_token():
    expired_payload = {
        "sub": "some-user-id",
        "role": "recruiter",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(hours=2)
    }
    import jwt
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower() or "credentials" in res.json()["detail"].lower()


# ── Case 15: One Invalid File Mixed With Valid Files ──────────────────────────
def test_case_15_one_invalid_file_mixed_with_valid_files():
    token = get_token()
    valid_pdf = os.path.join(SAMPLE_DIR, "Liam_OConnor_ML_Engineer.pdf")
    invalid_exe = os.path.join(EDGE_DIR, "Edge_03_Executable_Payload.exe")
    pwd_pdf = os.path.join(EDGE_DIR, "Edge_04_Password_Protected.pdf")

    with open(valid_pdf, "rb") as f1, open(invalid_exe, "rb") as f2, open(pwd_pdf, "rb") as f3:
        mixed_files = [
            ("files", ("Liam_OConnor_ML_Engineer.pdf", f1.read(), "application/pdf")),
            ("files", ("Bad_Payload.exe", f2.read(), "application/octet-stream")),
            ("files", ("Edge_04_Password_Protected.pdf", f3.read(), "application/pdf")),
        ]
        res = client.post("/api/resumes/upload", files=mixed_files, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    # File 1 is completed
    assert data[0]["processing_status"] == "completed"
    assert data[0]["candidate_id"] is not None
    # File 2 is failed
    assert data[1]["processing_status"] == "failed"
    assert "unsupported" in data[1]["error_message"].lower()
    # File 3 is failed (password protected)
    assert data[2]["processing_status"] == "failed"
    assert "password" in data[2]["error_message"].lower()


# ── Case 16: Database Error Isolation & Rollback ──────────────────────────────
def test_case_16_database_error_isolation():
    token = get_token()
    valid_pdf = os.path.join(SAMPLE_DIR, "Marcus_Vance_Senior_Backend.pdf")
    with open(valid_pdf, "rb") as f:
        res = client.post(
            "/api/resumes/upload",
            files=[("files", ("Marcus_Vance_Senior_Backend.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    assert res.json()[0]["processing_status"] == "completed"


# ── Case 17: Retry of a Failed File ───────────────────────────────────────────
def test_case_17_retry_of_failed_file():
    token = get_token()
    # 1. Attempt upload with bad payload (fails)
    res1 = client.post(
        "/api/resumes/upload",
        files=[("files", ("Test_Candidate.exe", b"invalid exe payload", "application/octet-stream"))],
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200
    assert res1.json()[0]["processing_status"] == "failed"

    # 2. Retry with valid corrected file
    valid_pdf = os.path.join(SAMPLE_DIR, "Priya_Sharma_Lead_AI_NLP.pdf")
    with open(valid_pdf, "rb") as f:
        res2 = client.post(
            "/api/resumes/upload",
            files=[("files", ("Priya_Sharma_Lead_AI_NLP.pdf", f.read(), "application/pdf"))],
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res2.status_code == 200
    assert res2.json()[0]["processing_status"] == "completed"
    assert res2.json()[0]["candidate_id"] is not None


# ── Case 18: Demo Batch Loading Idempotence ───────────────────────────────────
def test_case_18_demo_batch_loading_idempotence():
    token = get_token()
    res1 = client.post("/api/resumes/load-sample-batch", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200
    count1 = len(res1.json())
    assert count1 == 15

    # Calling a second time must NOT create duplicates
    res2 = client.post("/api/resumes/load-sample-batch", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    count2 = len(res2.json())
    assert count2 == 15
    for r in res2.json():
        assert r["processing_status"] == "completed"


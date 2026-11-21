"""Live upload test against running backend"""
import requests

BASE = "http://localhost:8000/api"

# Login
resp = requests.post(f"{BASE}/auth/login", json={"email": "admin@talentmatch.ai", "password": "Admin@123456"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== RESUME UPLOAD TEST ===")

# Test 1: Single PDF
files = [("files", ("Alex_Chen_Senior_FullStack.pdf", open("sample_resumes/Alex_Chen_Senior_FullStack.pdf", "rb"), "application/pdf"))]
r = requests.post(f"{BASE}/resumes/upload", headers=headers, files=files)
data = r.json()
print(f"Test 1 - Single PDF: status={r.status_code}, count={len(data)}")
for d in data:
    print(f"  {d['original_filename']}: {d['processing_status']} | candidate_id={d.get('candidate_id')}")

# Test 2: Multiple files (PDF + DOCX)
files2 = [
    ("files", ("Priya_Sharma_Lead_AI_NLP.pdf", open("sample_resumes/Priya_Sharma_Lead_AI_NLP.pdf", "rb"), "application/pdf")),
    ("files", ("Carlos_Rivera_Infra_Engineer.docx", open("sample_resumes/Carlos_Rivera_Infra_Engineer.docx", "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
]
r2 = requests.post(f"{BASE}/resumes/upload", headers=headers, files=files2)
data2 = r2.json()
print(f"\nTest 2 - Multi-file (PDF+DOCX): status={r2.status_code}, count={len(data2)}")
for d in data2:
    print(f"  {d['original_filename']}: {d['processing_status']} | error={d.get('error_message', 'None')}")

# Test 3: Unsupported file type
files3 = [("files", ("test.exe", b"MZ\x90\x00", "application/octet-stream"))]
r3 = requests.post(f"{BASE}/resumes/upload", headers=headers, files=files3)
data3 = r3.json()
print(f"\nTest 3 - Unsupported type: status={r3.status_code}")
for d in data3:
    print(f"  {d['original_filename']}: {d['processing_status']} | error={d.get('error_message', '')}")

# Test 4: Empty file  
files4 = [("files", ("empty.pdf", b"", "application/pdf"))]
r4 = requests.post(f"{BASE}/resumes/upload", headers=headers, files=files4)
data4 = r4.json()
print(f"\nTest 4 - Empty file: status={r4.status_code}")
for d in data4:
    print(f"  {d['original_filename']}: {d['processing_status']} | error={d.get('error_message', '')}")

# Test 5: Dashboard stats after uploads
dash = requests.get(f"{BASE}/analytics/dashboard", headers=headers).json()
print(f"\n=== DASHBOARD AFTER UPLOADS ===")
print(f"total_candidates={dash['total_candidates']}, total_resumes={dash['total_resumes']}, total_jobs={dash['total_jobs']}")

print("\nAll tests completed.")

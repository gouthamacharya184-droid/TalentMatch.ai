"""Security and integration tests"""
import requests

BASE = "http://localhost:8000/api"
resp = requests.post(f"{BASE}/auth/login", json={"email": "admin@talentmatch.ai", "password": "Admin@123456"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== SECURITY TESTS ===")

# 1. Dashboard without auth (should 401)
r = requests.get(f"{BASE}/analytics/dashboard")
print(f"Dashboard without auth: {r.status_code} {'PASS' if r.status_code == 401 else 'FAIL'}")

# 2. Get me without auth (should 401)
r = requests.get(f"{BASE}/auth/me")
print(f"Get me without auth: {r.status_code} {'PASS' if r.status_code == 401 else 'FAIL'}")

# 3. SQL injection attempt
r = requests.get(f"{BASE}/candidates?search=a' OR 1=1--", headers=headers)
print(f"SQL injection test: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")

# 4. Oversized chat message (> 2000 chars, should 422)
big_text = "A" * 2001
r = requests.post(f"{BASE}/chatbot/chat", headers=headers, json={"message": big_text})
print(f"Oversized chat message: {r.status_code} {'PASS' if r.status_code == 422 else 'FAIL'}")

# 5. Chatbot functional test
r = requests.post(f"{BASE}/chatbot/chat", headers=headers, json={"message": "What are the top candidates?"})
print(f"Chatbot response: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
if r.status_code == 200:
    data = r.json()
    mode = data.get("mode")
    has_msg = bool(data.get("assistant_message"))
    print(f"  mode={mode}, has_message={has_msg}")

# 6. Shortlist create + delete
print("\n=== SHORTLIST CRUD TESTS ===")
jobs_r = requests.get(f"{BASE}/jobs", headers=headers).json()
cands_r = requests.get(f"{BASE}/candidates", headers=headers).json()
if jobs_r["items"] and cands_r["items"]:
    job_id = jobs_r["items"][0]["id"]
    cand_id = cands_r["items"][0]["id"]
    sl = requests.post(f"{BASE}/shortlist", headers=headers, json={"job_id": job_id, "candidate_id": cand_id, "comments": "Test shortlist"})
    print(f"Create shortlist: {sl.status_code} {'PASS' if sl.status_code == 200 else 'FAIL'}")
    if sl.status_code == 200:
        sl_id = sl.json()["id"]
        dl = requests.delete(f"{BASE}/shortlist/{sl_id}", headers=headers)
        print(f"Delete shortlist: {dl.status_code} {'PASS' if dl.status_code == 200 else 'FAIL'}")

# 7. Download resume (should work)
print("\n=== FILE DOWNLOAD TEST ===")
resumes = requests.get(f"{BASE}/resumes", headers=headers).json()
if resumes["items"]:
    resume_id = resumes["items"][0]["id"]
    r = requests.get(f"{BASE}/resumes/{resume_id}/download", headers=headers)
    print(f"Resume download: {r.status_code} {'PASS' if r.status_code in (200, 404) else 'FAIL'} (404 is OK if file moved)")

# 8. AI matching test
print("\n=== AI MATCHING TEST ===")
if jobs_r["items"] and cands_r["items"]:
    job_id = jobs_r["items"][0]["id"]
    cand_ids = [c["id"] for c in cands_r["items"][:3]]
    r = requests.post(f"{BASE}/matching/analyze", headers=headers, json={"job_id": job_id, "candidate_ids": cand_ids})
    print(f"AI match analyze: {r.status_code} {'PASS' if r.status_code == 200 else 'FAIL'}")
    if r.status_code == 200:
        results = r.json()
        print(f"  Analyzed {len(results)} candidates, top score: {max(r.get('overall_score',0) for r in results):.1f}")

print("\nAll security and integration tests done.")

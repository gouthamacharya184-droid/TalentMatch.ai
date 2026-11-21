"""
TalantMatch.ai - Comprehensive API Test Suite
Runs against live server at http://localhost:8000
"""
import urllib.request
import json
import urllib.parse
import urllib.error
import sys

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
results = []

def req(method, path, data=None, headers=None, timeout=30):
    url = BASE + path
    h = headers or {}
    body = None
    if data:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            ct = r.headers.get("Content-Type", "")
            raw = r.read()
            if "json" in ct:
                return r.status, json.loads(raw)
            return r.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, str(e)
    except Exception as ex:
        return 0, str(ex)

def check(name, condition, actual=None, expect=None):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    extra = ""
    if actual is not None:
        extra = f" | got={actual}"
    if expect is not None:
        extra += f" | expect={expect}"
    print(f"  [{status}] {name}{extra}")
    results.append({"name": name, "status": status, "actual": str(actual)[:120]})

print("=" * 60)
print("TalantMatch.ai - API Test Suite")
print("=" * 60)

# ─────────────────────────────────────────────────────────────
print("\n=== 1. HEALTH CHECK ===")
s, r = req("GET", "/health")
check("Health endpoint returns 200", s == 200, s, 200)
check("Database connected", isinstance(r, dict) and r.get("database") == "connected", r.get("database") if isinstance(r, dict) else r)

# ─────────────────────────────────────────────────────────────
print("\n=== 2. AUTH TESTS ===")

# Valid login
s, r = req("POST", "/api/auth/login", {"email": "recruiter@talentmatch.ai", "password": "Recruiter@123456"})
check("Login with valid creds returns 200", s == 200, s, 200)
check("Login response contains access_token", isinstance(r, dict) and bool(r.get("access_token")), bool(r.get("access_token")) if isinstance(r, dict) else False)
token = r.get("access_token", "") if isinstance(r, dict) else ""
auth = {"Authorization": f"Bearer {token}"}

# Invalid password
s, r = req("POST", "/api/auth/login", {"email": "recruiter@talentmatch.ai", "password": "WrongPassword!"})
check("Login with wrong password returns 401", s == 401, s, 401)

# Non-existent user
s, r = req("POST", "/api/auth/login", {"email": "doesnotexist@nowhere.com", "password": "anything"})
check("Login with non-existent email returns 401/404", s in [401, 404], s)

# Auth/me with token
s, r = req("GET", "/api/auth/me", headers=auth)
check("GET /auth/me with valid token returns 200", s == 200, s, 200)
check("GET /auth/me returns correct email", isinstance(r, dict) and r.get("email") == "recruiter@talentmatch.ai", r.get("email") if isinstance(r, dict) else r)

# Auth/me without token
s, r = req("GET", "/api/auth/me")
check("GET /auth/me without token returns 401", s == 401, s, 401)

# Register new user
s, r = req("POST", "/api/auth/register", {"full_name": "Audit Tester", "email": "auditbot@test.com", "password": "AuditTest123"})
check("Register new user returns 200 or 400 (already exists)", s in [200, 400], s)

# SQL injection in login
s, r = req("POST", "/api/auth/login", {"email": "' OR '1'='1", "password": "' OR '1'='1"})
check("SQL injection in login blocked (not 200)", s != 200, s)

# Empty credentials
s, r = req("POST", "/api/auth/login", {"email": "", "password": ""})
check("Empty credentials rejected (not 200)", s != 200, s)

# Token refresh
s, r = req("POST", "/api/auth/refresh", headers={"Authorization": f"Bearer {token}"})
check("Token refresh works", s == 200, s)
refresh_token = r.get("access_token", "") if isinstance(r, dict) else ""
if refresh_token:
    token = refresh_token
    auth = {"Authorization": f"Bearer {token}"}

# ─────────────────────────────────────────────────────────────
print("\n=== 3. ANALYTICS AUTH CHECK (Security) ===")
s, r = req("GET", "/api/analytics/dashboard")
check("Analytics dashboard without auth - SECURITY: should be 401", s == 401, s, "401 (or 200=VULN)")
s, r = req("GET", "/api/analytics/dashboard", headers=auth)
check("Analytics dashboard with auth returns 200", s == 200, s, 200)
if s == 200 and isinstance(r, dict):
    check("Analytics dashboard has total_jobs key", "total_jobs" in r, list(r.keys())[:5])

s, r = req("GET", "/api/analytics/history")
check("Analytics history without auth - SECURITY: should be 401", s == 401, s, "401 (or 200=VULN)")

# ─────────────────────────────────────────────────────────────
print("\n=== 4. NOTIFICATIONS AUTH CHECK (Security) ===")
s, r = req("GET", "/api/notifications")
check("Notifications without auth - SECURITY: should be 401", s == 401, s, "401 (or 200=VULN)")
s, r = req("GET", "/api/notifications", headers=auth)
check("Notifications with auth returns 200", s == 200, s, 200)

# ─────────────────────────────────────────────────────────────
print("\n=== 5. JOB CRUD ===")
s, r = req("GET", "/api/jobs")
check("GET /jobs returns 200", s == 200, s, 200)
check("Jobs response has total field", isinstance(r, dict) and "total" in r, r.get("total") if isinstance(r, dict) else r)
jobs = r.get("items", []) if isinstance(r, dict) else []
check("At least 1 job exists", len(jobs) >= 1, len(jobs))

# Create job
s, r = req("POST", "/api/jobs", {
    "title": "AUDIT TEST Job - Delete Me",
    "company": "AuditCo",
    "description": "Python Django REST API automation testing devops",
    "min_experience": 2.0,
    "location": "Remote",
    "education_req": "Bachelor"
}, headers=auth)
check("Create job returns 200", s == 200, s, 200)
test_job_id = r.get("id") if isinstance(r, dict) else None
check("Created job has an ID", bool(test_job_id), test_job_id)

if test_job_id:
    s, r = req("GET", f"/api/jobs/{test_job_id}")
    check("GET job by ID returns 200", s == 200, s, 200)
    check("GET job has correct title", isinstance(r, dict) and "AUDIT TEST" in r.get("title", ""), r.get("title") if isinstance(r, dict) else r)

    # Create job without auth (should be allowed or 401)
    s, r = req("POST", "/api/jobs", {"title": "No Auth Job", "company": "X", "description": "Test", "min_experience": 1.0})
    check("Create job without auth - returns 200 or 401", s in [200, 401], s)

    # Update job
    s, r = req("PUT", f"/api/jobs/{test_job_id}", {
        "title": "AUDIT TEST Job UPDATED",
        "company": "AuditCo",
        "description": "Updated description Python Docker Kubernetes",
        "min_experience": 3.0
    }, headers=auth)
    check("Update job returns 200", s == 200, s, 200)

    # Extract requirements
    s, r = req("POST", f"/api/jobs/{test_job_id}/extract-requirements", headers=auth)
    check("Extract requirements returns 200", s == 200, s, 200)
    check("Extract returns list", isinstance(r, list), type(r).__name__)
    
    # Delete test job
    s, r = req("DELETE", f"/api/jobs/{test_job_id}", headers=auth)
    check("Delete job returns 200", s == 200, s, 200)
    s, r = req("GET", f"/api/jobs/{test_job_id}")
    check("Deleted job returns 404", s == 404, s, 404)

# ─────────────────────────────────────────────────────────────
print("\n=== 6. CANDIDATES ===")
s, r = req("GET", "/api/candidates?limit=5")
check("GET /candidates returns 200", s == 200, s, 200)
check("Candidates response has total", isinstance(r, dict) and "total" in r, r.get("total") if isinstance(r, dict) else r)
candidates = r.get("items", []) if isinstance(r, dict) else []
check("At least 1 candidate exists", len(candidates) >= 1, len(candidates))

s, r = req("GET", "/api/candidates?search=Alex")
check("Candidate search returns 200", s == 200, s, 200)

s, r = req("GET", "/api/candidates?min_score=80")
check("Candidate filter by min_score returns 200", s == 200, s, 200)

s, r = req("GET", "/api/candidates?limit=5&offset=0&sort_by=match_score&sort_order=desc")
check("Candidate sort returns 200", s == 200, s, 200)

if candidates:
    cid = candidates[0]["id"]
    s, r = req("GET", f"/api/candidates/{cid}")
    check("GET candidate by ID returns 200", s == 200, s, 200)
    s, r = req("GET", f"/api/candidates/{cid}/skills")
    check("GET candidate skills returns 200", s == 200, s, 200)
    # IDOR test - access another user's data without token
    s, r = req("GET", f"/api/candidates/{cid}")
    check("GET candidate without auth - accessible or 401", s in [200, 401], s)

# ─────────────────────────────────────────────────────────────
print("\n=== 7. MATCHING & RANKINGS ===")
s, r = req("GET", "/api/jobs")
jobs = r.get("items", []) if isinstance(r, dict) else []
if jobs:
    job_id = jobs[0]["id"]
    s, r = req("GET", f"/api/matching/rankings/{job_id}")
    check("GET rankings returns 200", s == 200, s, 200)
    check("Rankings returns list", isinstance(r, list), type(r).__name__)
    
    s, r = req("GET", f"/api/matching/results/{job_id}")
    check("GET results returns 200", s == 200, s, 200)

    s, r = req("GET", f"/api/matching/analysis/{job_id}")
    check("GET analysis returns 200", s in [200, 404], s)

# ─────────────────────────────────────────────────────────────
print("\n=== 8. SHORTLIST ===")
s, r = req("GET", "/api/candidates?limit=2")
cands = r.get("items", []) if isinstance(r, dict) else []
s, r = req("GET", "/api/jobs")
jobs = r.get("items", []) if isinstance(r, dict) else []

if cands and jobs:
    cid = cands[0]["id"]
    jid = jobs[0]["id"]
    
    s, r = req("POST", f"/api/shortlist/{jid}/{cid}", headers=auth)
    check("Add to shortlist returns 200", s == 200, s, 200)
    
    s, r = req("GET", f"/api/shortlist/status/{jid}/{cid}", headers=auth)
    check("Shortlist status returns 200", s == 200, s, 200)
    check("Candidate is shortlisted", isinstance(r, dict) and r.get("is_shortlisted") == True, r.get("is_shortlisted") if isinstance(r, dict) else r)
    
    # Add recruiter note
    s, r = req("POST", f"/api/shortlist/{jid}/{cid}/notes", {"note": "Great candidate for the role"}, headers=auth)
    check("Add recruiter note returns 200", s == 200, s, 200)
    
    s, r = req("DELETE", f"/api/shortlist/{jid}/{cid}", headers=auth)
    check("Remove from shortlist returns 200", s == 200, s, 200)
    
    s, r = req("GET", f"/api/shortlist/status/{jid}/{cid}", headers=auth)
    check("After removal, shortlist status is False", isinstance(r, dict) and r.get("is_shortlisted") == False, r.get("is_shortlisted") if isinstance(r, dict) else r)

# ─────────────────────────────────────────────────────────────
print("\n=== 9. CHATBOT ===")
s, r = req("POST", "/api/chatbot/chat", {"message": "What is TalentMatch?"}, headers=auth)
check("Chatbot returns 200", s == 200, s, 200)
check("Chatbot returns a response text", isinstance(r, dict) and bool(r.get("response") or r.get("message") or r.get("text")), list(r.keys()) if isinstance(r, dict) else r)

s, r = req("GET", "/api/chatbot/welcome", headers=auth)
check("Chatbot welcome returns 200", s == 200, s, 200)

s, r = req("GET", "/api/chatbot/suggestions", headers=auth)
check("Chatbot suggestions returns 200", s == 200, s, 200)

# ─────────────────────────────────────────────────────────────
print("\n=== 10. COMPARISON ===")
s, r = req("GET", "/api/candidates?limit=3")
cands = r.get("items", []) if isinstance(r, dict) else []
s, r = req("GET", "/api/jobs")
jobs = r.get("items", []) if isinstance(r, dict) else []

if len(cands) >= 2 and jobs:
    ids = [c["id"] for c in cands[:3]]
    jid = jobs[0]["id"]
    s, r = req("POST", "/api/comparison/compare", {"candidate_ids": ids, "job_id": jid}, headers=auth)
    check("Compare candidates returns 200", s == 200, s, 200)
    if isinstance(r, dict):
        has_data = bool(r.get("candidates") or r.get("comparison") or r.get("data"))
        check("Compare response has data", has_data, list(r.keys())[:5])
    elif isinstance(r, list):
        check("Compare response is a non-empty list", len(r) > 0, len(r))

# ─────────────────────────────────────────────────────────────
print("\n=== 11. ANALYTICS REPORTS ===")
s, r = req("GET", "/api/jobs")
jobs = r.get("items", []) if isinstance(r, dict) else []
if jobs:
    jid = jobs[0]["id"]
    s, r = req("GET", f"/api/analytics/reports/{jid}?format=csv", headers=auth)
    check("Analytics CSV report returns 200", s == 200, s, 200)

# ─────────────────────────────────────────────────────────────
print("\n=== 12. RESUMES ===")
s, r = req("GET", "/api/resumes", headers=auth)
check("GET /resumes returns 200", s == 200, s, 200)
if isinstance(r, dict):
    check("Resumes has total field", "total" in r, list(r.keys())[:5])

# ─────────────────────────────────────────────────────────────
print("\n=== 13. SECURITY - NON-EXISTENT RESOURCE ===")
s, r = req("GET", "/api/jobs/nonexistent-id-99999")
check("Non-existent job returns 404 (not 500)", s in [404, 422], s)
s, r = req("GET", "/api/candidates/nonexistent-id-99999")
check("Non-existent candidate returns 404 (not 500)", s in [404, 422], s)

# ─────────────────────────────────────────────────────────────
print("\n=== 14. SECURITY HEADERS ===")
s, r = req("GET", "/health")
# check response headers by making a raw request
import http.client
conn = http.client.HTTPConnection("localhost", 8000, timeout=5)
conn.request("GET", "/health")
resp = conn.getresponse()
headers_dict = dict(resp.getheaders())
conn.close()
check("X-Content-Type-Options header present", "x-content-type-options" in {k.lower(): v for k, v in headers_dict.items()}, list(headers_dict.keys())[:6])
check("X-Frame-Options header present", "x-frame-options" in {k.lower(): v for k, v in headers_dict.items()}, list(headers_dict.keys())[:6])

# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"TOTAL: {PASS + FAIL} tests | PASSED: {PASS} | FAILED: {FAIL}")
print("=" * 60)

# Save JSON results
with open("audit_test_results.json", "w") as f:
    json.dump({"pass": PASS, "fail": FAIL, "results": results}, f, indent=2)
print(f"\nResults saved to audit_test_results.json")

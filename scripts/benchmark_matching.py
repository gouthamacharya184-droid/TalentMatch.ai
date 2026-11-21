import urllib.request
import json
import time

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login', 
    data=json.dumps({'email': 'recruiter@talentmatch.ai', 'password': 'Recruiter@123456'}).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as r:
    token = json.loads(r.read())['access_token']

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

jobs_req = urllib.request.Request('http://127.0.0.1:8000/api/jobs', headers=headers)
jobs = json.loads(urllib.request.urlopen(jobs_req).read())['items']

cands_req = urllib.request.Request('http://127.0.0.1:8000/api/candidates?limit=20', headers=headers)
cands = json.loads(urllib.request.urlopen(cands_req).read())['items']

job_id = jobs[0]['id']
cand_ids = [c['id'] for c in cands]

print(f"Testing matching for Job: {jobs[0]['title']}")
print(f"Total candidates available: {len(cand_ids)}")

# Test 1 candidate
t0 = time.time()
match_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/matching/analyze', 
    data=json.dumps({'job_id': job_id, 'candidate_ids': cand_ids[:1]}).encode(),
    headers=headers
)
with urllib.request.urlopen(match_req) as r:
    res1 = json.loads(r.read())
t1 = time.time()
print(f"1 candidate: {t1 - t0:.2f} seconds")

# Test 5 candidates
t0 = time.time()
match_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/matching/analyze', 
    data=json.dumps({'job_id': job_id, 'candidate_ids': cand_ids[:5]}).encode(),
    headers=headers
)
with urllib.request.urlopen(match_req) as r:
    res5 = json.loads(r.read())
t2 = time.time()
print(f"5 candidates: {t2 - t0:.2f} seconds (average {(t2 - t0)/5:.2f}s per candidate)")

# Test 15 candidates
if len(cand_ids) >= 15:
    t0 = time.time()
    match_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/matching/analyze', 
        data=json.dumps({'job_id': job_id, 'candidate_ids': cand_ids[:15]}).encode(),
        headers=headers
    )
    with urllib.request.urlopen(match_req) as r:
        res15 = json.loads(r.read())
    t3 = time.time()
    print(f"15 candidates: {t3 - t0:.2f} seconds (average {(t3 - t0)/15:.2f}s per candidate)")

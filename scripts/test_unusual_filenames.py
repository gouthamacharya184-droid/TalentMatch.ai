import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=json.dumps({'email': 'recruiter@talentmatch.ai', 'password': 'Recruiter@123456'}).encode(),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as r:
    token = json.loads(r.read())['access_token']

boundary = '----WebKitFormBoundaryUnusualNames7MA4YWxkTrZu0gW'
body = bytearray()

test_filenames = [
    'Resume of John Doe (Senior Developer).txt',
    'Jose_Muller_CV_2026.txt',
    'resume.final.v2.candidate.txt',
    'CV#2026-Test@v1.txt'
]

sample_txt = b'Maria Gomez\nEmail: maria.gomez@example.com\nPhone: +1 555 123 4567\nSkills: Python, React, FastAPI, SQL\nExperience: 5 years Software Engineer\nEducation: BS in Computer Science\n'

for fn in test_filenames:
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="files"; filename="{fn}"\r\n'.encode('utf-8'))
    body.extend(b'Content-Type: text/plain\r\n\r\n')
    body.extend(sample_txt)
    body.extend(b'\r\n')

body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

up_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/resumes/upload',
    data=body,
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
)

with urllib.request.urlopen(up_req) as r:
    data = json.loads(r.read())
    print(f'Uploaded {len(data)} resumes with unusual filenames:')
    for d in data:
        print(f'  Filename: {d["original_filename"]} -> Status: {d["processing_status"]}, Candidate ID: {d.get("candidate_id")}')

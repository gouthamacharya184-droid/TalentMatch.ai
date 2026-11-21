import sqlite3
import os

tables_to_clear = [
    'score_breakdowns',
    'matching_analyses',
    'shortlists',
    'recruiter_notes',
    'candidate_skills',
    'resumes',
    'candidates',
    'job_requirements',
    'jobs',
    'notifications',
    'activity_logs'
]

for db_path in ['backend/talentmatch.db', 'talentmatch.db']:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('PRAGMA foreign_keys = OFF;')
        for tbl in tables_to_clear:
            cur.execute(f'DELETE FROM {tbl};')
        cur.execute("DELETE FROM users WHERE email NOT IN ('admin@talentmatch.ai', 'recruiter@talentmatch.ai');")
        conn.commit()
        cur.execute('VACUUM;')
        conn.close()
        print(f'Wiped data in {db_path}')

# Clean storage/uploads
uploads_dir = 'storage/uploads'
if os.path.exists(uploads_dir):
    deleted_files = 0
    for f in os.listdir(uploads_dir):
        if f != '.gitkeep':
            p = os.path.join(uploads_dir, f)
            if os.path.isfile(p):
                os.remove(p)
                deleted_files += 1
    print(f'Deleted {deleted_files} files from {uploads_dir}')


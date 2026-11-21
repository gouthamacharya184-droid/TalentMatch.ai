"""
Non-destructive database migration script for TalentMatch.ai v2.0 Enterprise Agentic Platform.
Safely adds missing columns and creates new tables without altering or deleting existing data.
"""
import os
import sqlite3
import sys

def migrate_sqlite_db(db_path: str):
    print(f"Checking database at: {db_path}")
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist, skipping.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    def get_columns(table_name: str):
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]

    # 1. jobs table enhancements
    job_cols = get_columns("jobs")
    if "campaign_id" not in job_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN campaign_id VARCHAR(36)")
        print("Added jobs.campaign_id")
    if "scoring_weights" not in job_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN scoring_weights JSON")
        print("Added jobs.scoring_weights")
    if "criteria_approved" not in job_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN criteria_approved BOOLEAN DEFAULT 0")
        print("Added jobs.criteria_approved")
    if "criteria_approved_at" not in job_cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN criteria_approved_at DATETIME")
        print("Added jobs.criteria_approved_at")

    # 2. job_requirements enhancements
    if "job_requirements" in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        jr_cols = get_columns("job_requirements")
        if "weight" not in jr_cols:
            cur.execute("ALTER TABLE job_requirements ADD COLUMN weight FLOAT DEFAULT 1.0")
            print("Added job_requirements.weight")

    # 3. candidates table enhancements
    cand_cols = get_columns("candidates")
    if "projects" not in cand_cols:
        cur.execute("ALTER TABLE candidates ADD COLUMN projects JSON")
        print("Added candidates.projects")
    if "certifications" not in cand_cols:
        cur.execute("ALTER TABLE candidates ADD COLUMN certifications JSON")
        print("Added candidates.certifications")

    # 4. candidate_skills table enhancements
    cs_cols = get_columns("candidate_skills")
    if "evidence_type" not in cs_cols:
        cur.execute("ALTER TABLE candidate_skills ADD COLUMN evidence_type VARCHAR(50) DEFAULT 'explicit'")
        print("Added candidate_skills.evidence_type")

    # 5. resumes table enhancements
    res_cols = get_columns("resumes")
    if "page_count" not in res_cols:
        cur.execute("ALTER TABLE resumes ADD COLUMN page_count INTEGER DEFAULT 1")
        print("Added resumes.page_count")
    if "content_hash" not in res_cols:
        cur.execute("ALTER TABLE resumes ADD COLUMN content_hash VARCHAR(64)")
        print("Added resumes.content_hash")
    if "page_texts" not in res_cols:
        cur.execute("ALTER TABLE resumes ADD COLUMN page_texts JSON")
        print("Added resumes.page_texts")

    # 6. matching_analyses table enhancements
    ma_cols = get_columns("matching_analyses")
    if "evaluation_run_id" not in ma_cols:
        cur.execute("ALTER TABLE matching_analyses ADD COLUMN evaluation_run_id VARCHAR(36)")
        print("Added matching_analyses.evaluation_run_id")
    if "projects_score" not in ma_cols:
        cur.execute("ALTER TABLE matching_analyses ADD COLUMN projects_score FLOAT DEFAULT 0.0")
        print("Added matching_analyses.projects_score")
    if "preferred_score" not in ma_cols:
        cur.execute("ALTER TABLE matching_analyses ADD COLUMN preferred_score FLOAT DEFAULT 0.0")
        print("Added matching_analyses.preferred_score")
    if "weights_used" not in ma_cols:
        cur.execute("ALTER TABLE matching_analyses ADD COLUMN weights_used JSON")
        print("Added matching_analyses.weights_used")
    if "confidence_score" not in ma_cols:
        cur.execute("ALTER TABLE matching_analyses ADD COLUMN confidence_score FLOAT DEFAULT 0.90")
        print("Added matching_analyses.confidence_score")
    if "uncertainty_notes" not in ma_cols:
        cur.execute("ALTER TABLE matching_analyses ADD COLUMN uncertainty_notes TEXT")
        print("Added matching_analyses.uncertainty_notes")

    # 7. score_breakdowns table enhancements
    sb_cols = get_columns("score_breakdowns")
    if "weight_percentage" not in sb_cols:
        cur.execute("ALTER TABLE score_breakdowns ADD COLUMN weight_percentage FLOAT DEFAULT 0.0")
        print("Added score_breakdowns.weight_percentage")

    conn.commit()
    conn.close()
    print(f"Migration completed for {db_path} successfully.")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, base_dir)
    
    # 1. Run raw column alters
    migrate_sqlite_db(os.path.join(base_dir, "talentmatch.db"))
    root_db = os.path.abspath(os.path.join(base_dir, "..", "talentmatch.db"))
    if os.path.exists(root_db):
        migrate_sqlite_db(root_db)

    # 2. Use SQLAlchemy Base.metadata.create_all to create new tables
    from app.database.session import Base, engine
    import app.models.all_models
    print("Creating new tables via SQLAlchemy Base.metadata.create_all...")
    Base.metadata.create_all(bind=engine)
    print("All enterprise tables verified and created successfully.")

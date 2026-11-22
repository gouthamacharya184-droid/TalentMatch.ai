import logging
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.all_models import (
    User,
    Job,
    JobRequirement,
    Candidate,
    CandidateSkill,
    Resume,
    MatchingAnalysis,
    Shortlist,
    Notification,
    ActivityLog
)
from app.ai_engine.matching_engine import MatchingEngine
from app.ai_engine.interview_questions import InterviewQuestionGenerator
from app.ai_engine.insights import CandidateInsights

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"
RECRUITER_USER_ID = "00000000-0000-0000-0000-000000000002"


def seed_database(db: Session, fast_mode: bool = False):
    """Seed initial demo users, realistic job descriptions, and candidate resumes."""
    # 1. Ensure demo users exist and credentials match demo fill buttons
    admin = db.query(User).filter(User.email == "admin@talentmatch.ai").first()
    if not admin:
        admin = User(
            id=ADMIN_USER_ID,
            email="admin@talentmatch.ai",
            hashed_password=hash_password("Admin@123456"),
            full_name="Alex Mercer (Super Admin)",
            role="super_admin",
            is_active=True
        )
        db.add(admin)
    else:
        if not verify_password("Admin@123456", admin.hashed_password):
            admin.hashed_password = hash_password("Admin@123456")
        admin.is_active = True
        admin.role = "super_admin"

    recruiter = db.query(User).filter(User.email == "recruiter@talentmatch.ai").first()
    if not recruiter:
        recruiter = User(
            id=RECRUITER_USER_ID,
            email="recruiter@talentmatch.ai",
            hashed_password=hash_password("Recruiter@123456"),
            full_name="Sarah Jenkins (Senior Recruiter)",
            role="recruiter",
            is_active=True
        )
        db.add(recruiter)
    else:
        if not verify_password("Recruiter@123456", recruiter.hashed_password):
            recruiter.hashed_password = hash_password("Recruiter@123456")
        recruiter.is_active = True

    db.commit()

    # Fast exit for cold starts or if database already populated with jobs
    if fast_mode or db.query(Job).count() > 0:
        return

    logger.info("Seeding realistic recruitment jobs and candidates...")

    job1 = Job(
        user_id=recruiter.id,
        title="Senior Full-Stack Engineer",
        company="AVOM Consultants",
        location="Remote (US / Global)",
        employment_type="Full-time",
        min_experience=4.0,
        education_req="Bachelor's Degree in Computer Science or related",
        description="""We are seeking a Senior Full-Stack Engineer to architect and build high-performance web applications.
The ideal candidate will have strong expertise in Python (FastAPI or Django) for robust REST API backend services, and modern React with TypeScript on the frontend.
Experience with PostgreSQL database modeling, query optimization, Docker containerization, and AWS cloud deployment is essential.
Familiarity with CI/CD automation, unit testing, and agile collaboration is required.
Preferred skills include Redis caching, Tailwind CSS, and microservice architectures.""",
        status="active"
    )
    db.add(job1)

    job2 = Job(
        user_id=recruiter.id,
        title="Lead AI & NLP Engineer",
        company="Cognitive Systems Labs",
        location="San Francisco, CA / Hybrid",
        employment_type="Full-time",
        min_experience=5.0,
        education_req="Master's Degree in Computer Science or AI/ML",
        description="""Join our team as Lead AI & NLP Engineer to design semantic matching algorithms, vector embeddings, and LLM applications.
Requirements: In-depth Python proficiency, deep learning architectures (PyTorch or TensorFlow), Hugging Face Transformers, Sentence Transformers, and spaCy.
Hands-on experience with vector databases (Pinecone, Milvus or ChromaDB), RAG architectures, Scikit-learn, and MLOps pipelines (Docker, MLflow).
Strong grasp of cosine similarity metrics, statistical testing, and scalable model serving under FastAPI.""",
        status="active"
    )
    db.add(job2)
    db.commit()
    db.refresh(job1)
    db.refresh(job2)

    # Job 1 Requirements
    job1_reqs = [
        ("Python", "mandatory", "language"),
        ("FastAPI", "mandatory", "framework"),
        ("React", "mandatory", "framework"),
        ("TypeScript", "mandatory", "language"),
        ("PostgreSQL", "mandatory", "database"),
        ("Docker", "mandatory", "cloud_devops"),
        ("REST API", "mandatory", "tools_and_practices"),
        ("AWS", "preferred", "cloud_devops"),
        ("Tailwind CSS", "preferred", "frontend_frameworks"),
        ("Redis", "preferred", "databases"),
        ("CI/CD", "preferred", "cloud_devops"),
    ]
    for name, cat, stype in job1_reqs:
        db.add(JobRequirement(job_id=job1.id, skill_name=name, category=cat, skill_type=stype))

    # Job 2 Requirements
    job2_reqs = [
        ("Python", "mandatory", "language"),
        ("PyTorch", "mandatory", "ai_ml"),
        ("NLP", "mandatory", "ai_ml"),
        ("Machine Learning", "mandatory", "ai_ml"),
        ("Sentence Transformers", "mandatory", "ai_ml"),
        ("FastAPI", "mandatory", "backend_frameworks"),
        ("Scikit-learn", "preferred", "ai_ml"),
        ("Docker", "preferred", "cloud_devops"),
        ("Hugging Face", "preferred", "ai_ml"),
        ("RAG", "preferred", "ai_ml"),
    ]
    for name, cat, stype in job2_reqs:
        db.add(JobRequirement(job_id=job2.id, skill_name=name, category=cat, skill_type=stype))

    db.commit()

    # 3. Seed 12 Diverse Candidates with realistic resumes & skills
    sample_candidates = [
        {
            "name": "Marcus Vance",
            "email": "marcus.vance@techdev.io",
            "phone": "+1 (415) 890-2341",
            "location": "San Francisco, CA",
            "years": 6.5,
            "education": [{"degree": "B.S. in Computer Science", "institution": "UC Berkeley", "year": "2018"}],
            "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "AWS", "REST API", "Redis", "Tailwind CSS", "Git"],
            "bio": "Senior Full-Stack Developer with 6+ years designing scalable microservices with FastAPI and dynamic frontends with React and TypeScript. Heavy cloud deployment on AWS ECS."
        },
        {
            "name": "Elena Rostova",
            "email": "elena.rostova@datascience.net",
            "phone": "+1 (206) 555-0192",
            "location": "Seattle, WA",
            "years": 5.0,
            "education": [{"degree": "M.S. in Artificial Intelligence", "institution": "University of Washington", "year": "2019"}],
            "skills": ["Python", "PyTorch", "NLP", "Machine Learning", "Sentence Transformers", "FastAPI", "Scikit-learn", "Docker", "Hugging Face", "spaCy", "Git"],
            "bio": "NLP and Applied AI Engineer with 5 years experience creating semantic retrieval pipelines, transformers model fine-tuning, and production model serving."
        },
        {
            "name": "David Chen",
            "email": "david.chen.dev@cloudmail.org",
            "phone": "+1 (650) 441-9820",
            "location": "Austin, TX",
            "years": 4.5,
            "education": [{"degree": "B.Tech in Information Technology", "institution": "UT Austin", "year": "2020"}],
            "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker", "REST API", "Git", "Tailwind CSS"],
            "bio": "Full-Stack Software Engineer proficient in building responsive React applications and performant Python/FastAPI backend APIs. Strong database optimization."
        },
        {
            "name": "Priya Sharma",
            "email": "priya.sharma@aimlconsult.com",
            "phone": "+1 (408) 723-9114",
            "location": "San Jose, CA",
            "years": 7.0,
            "education": [{"degree": "M.S. in Computer Science", "institution": "Stanford University", "year": "2017"}],
            "skills": ["Python", "PyTorch", "TensorFlow", "NLP", "Machine Learning", "Sentence Transformers", "Scikit-learn", "Docker", "FastAPI", "Kubernetes", "RAG"],
            "bio": "Principal AI Researcher and ML Engineer specializing in Large Language Models, semantic search embeddings, and scalable inference infrastructure."
        },
        {
            "name": "Liam O'Connor",
            "email": "liam.oconnor@frontendeers.io",
            "phone": "+1 (617) 932-1102",
            "location": "Boston, MA",
            "years": 3.5,
            "education": [{"degree": "B.S. in Software Engineering", "institution": "Northeastern University", "year": "2021"}],
            "skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Redux", "Node.js", "REST API", "Git"],
            "bio": "Frontend specialist focused on React 19, TypeScript, and modern component systems. Moderate backend experience with Node.js and REST endpoints."
        },
        {
            "name": "Amina Al-Mansoor",
            "email": "amina.mansoor@backendpro.org",
            "phone": "+1 (312) 674-8891",
            "location": "Chicago, IL",
            "years": 5.5,
            "education": [{"degree": "B.S. in Computer Engineering", "institution": "University of Illinois Urbana-Champaign", "year": "2019"}],
            "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Docker", "AWS", "REST API", "Redis", "CI/CD", "Linux", "Git"],
            "bio": "Backend Architect with extensive background in Python microservices, distributed caching with Redis, relational schemas in PostgreSQL, and Dockerized deployments."
        },
        {
            "name": "Carlos Mendez",
            "email": "carlos.mendez@devopsphere.com",
            "phone": "+1 (720) 819-3304",
            "location": "Denver, CO",
            "years": 4.0,
            "education": [{"degree": "B.S. in Information Systems", "institution": "CU Boulder", "year": "2020"}],
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Python", "Terraform", "Git", "GitHub Actions"],
            "bio": "DevOps and Cloud Infrastructure Engineer. Expert in CI/CD pipeline automation, container orchestration, and Infrastructure as Code using Terraform."
        },
        {
            "name": "Sofia Lindqvist",
            "email": "sofia.lindqvist@nordicml.se",
            "phone": "+1 (212) 704-5182",
            "location": "New York, NY",
            "years": 3.0,
            "education": [{"degree": "M.S. in Data Science", "institution": "Columbia University", "year": "2021"}],
            "skills": ["Python", "Machine Learning", "Scikit-learn", "Pandas", "NumPy", "NLP", "FastAPI", "Git"],
            "bio": "Data Scientist with focus on predictive modeling, exploratory analysis, and NLP text classification using Scikit-learn and Pandas."
        },
        {
            "name": "Jordan Taylor",
            "email": "jordan.taylor@techlaunch.io",
            "phone": "+1 (503) 412-9981",
            "location": "Portland, OR",
            "years": 1.5,
            "education": [{"degree": "B.S. in Computer Science", "institution": "Oregon State", "year": "2023"}],
            "skills": ["Python", "JavaScript", "React", "HTML", "CSS", "Git"],
            "bio": "Junior Full-Stack Developer eager to grow in enterprise software development. Academic projects involving React web apps and Python scripts."
        },
        {
            "name": "Kavita Patel",
            "email": "kavita.patel@scalableweb.net",
            "phone": "+1 (919) 334-7812",
            "location": "Raleigh, NC",
            "years": 8.0,
            "education": [{"degree": "B.S. in Computer Science", "institution": "NC State", "year": "2016"}],
            "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "AWS", "REST API", "Microservices", "System Design", "Agile", "Git"],
            "bio": "Staff Full-Stack Engineer with 8 years of enterprise application architecture. Proven leader in designing cloud-native microservices with FastAPI and modular React."
        },
        {
            "name": "Tariq Edwards",
            "email": "tariq.edwards@datasystems.io",
            "phone": "+1 (404) 918-2231",
            "location": "Atlanta, GA",
            "years": 6.0,
            "education": [{"degree": "M.S. in Machine Learning", "institution": "Georgia Tech", "year": "2018"}],
            "skills": ["Python", "PyTorch", "NLP", "Sentence Transformers", "Machine Learning", "FastAPI", "Docker", "Scikit-learn", "Hugging Face", "Vector Embeddings"],
            "bio": "Senior NLP Engineer leading semantic search and information extraction systems for enterprise search catalogs using Transformer models."
        },
        {
            "name": "Zoe Kravitz",
            "email": "zoe.kravitz@webcraft.co",
            "phone": "+1 (305) 612-4490",
            "location": "Miami, FL",
            "years": 2.5,
            "education": [{"degree": "Associate Degree in Web Programming", "institution": "Miami Dade College", "year": "2022"}],
            "skills": ["JavaScript", "React", "HTML5", "CSS3", "Bootstrap", "Git"],
            "bio": "Frontend Web Developer with 2.5 years experience constructing landing pages, dashboards, and responsive web components using React and JavaScript."
        }
    ]

    use_fast = fast_mode or bool(os.environ.get("VERCEL"))
    if not use_fast:
        from app.ai_engine.matching_engine import MatchingEngine
        from app.ai_engine.interview_questions import InterviewQuestionGenerator
        from app.ai_engine.insights import CandidateInsights
        matching_engine = MatchingEngine()
        question_gen = InterviewQuestionGenerator()
        insights_gen = CandidateInsights()
    else:
        matching_engine = None
        question_gen = None
        insights_gen = None

    job1_data = {
        "title": job1.title,
        "company": job1.company,
        "description": job1.description,
        "min_experience": job1.min_experience,
        "education_req": job1.education_req,
        "requirements": [{"skill_name": n, "category": c, "skill_type": s} for n, c, s in job1_reqs]
    }

    job2_data = {
        "title": job2.title,
        "company": job2.company,
        "description": job2.description,
        "min_experience": job2.min_experience,
        "education_req": job2.education_req,
        "requirements": [{"skill_name": n, "category": c, "skill_type": s} for n, c, s in job2_reqs]
    }

    for idx, c_info in enumerate(sample_candidates):
        cand = Candidate(
            user_id=recruiter.id,
            name=c_info["name"],
            email=c_info["email"],
            phone=c_info["phone"],
            location=c_info["location"],
            total_experience_years=c_info["years"],
            education=c_info["education"],
            extracted_profile={
                "name": c_info["name"],
                "email": c_info["email"],
                "bio": c_info["bio"],
                "projects": [{"name": f"{c_info['skills'][0]} Platform", "description": f"Architected high-scale platform utilizing {', '.join(c_info['skills'][:4])}."}]
            },
            status="analyzed" if idx > 3 else "shortlisted"
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)

        # Resume record
        res = Resume(
            candidate_id=cand.id,
            original_filename=f"{cand.name.replace(' ', '_')}_Resume.pdf",
            stored_filename=f"demo_{cand.id}.pdf",
            file_path=f"storage/uploads/demo_{cand.id}.pdf",
            file_type="pdf",
            file_size=1024 * 145,
            raw_text=f"{c_info['name']}\n{c_info['email']} | {c_info['phone']} | {c_info['location']}\n\nSummary:\n{c_info['bio']}\n\nTechnical Skills:\n{', '.join(c_info['skills'])}\n\nExperience:\n{c_info['years']} years in professional software engineering roles.",
            processing_status="completed"
        )
        db.add(res)

        # Skills
        for s in c_info["skills"]:
            db.add(CandidateSkill(candidate_id=cand.id, skill_name=s, proficiency_level="advanced", source="extracted"))

        db.commit()

        if use_fast:
            cand_skill_set = {s.lower() for s in c_info["skills"]}
            j1_reqs_lower = {r[0].lower() for r in job1_reqs}
            matched_j1 = [s for s in c_info["skills"] if s.lower() in j1_reqs_lower]
            missing_j1 = [r[0] for r in job1_reqs if r[0].lower() not in cand_skill_set]
            skill_ratio1 = len(matched_j1) / max(len(job1_reqs), 1)
            tech_score1 = round(min(100.0, skill_ratio1 * 100), 1)
            overall1 = round(tech_score1 * 0.5 + min(100.0, (cand.total_experience_years / 5.0) * 80) * 0.3 + 18.0, 1)

            analysis1 = MatchingAnalysis(
                job_id=job1.id,
                candidate_id=cand.id,
                user_id=recruiter.id,
                overall_score=overall1,
                technical_score=tech_score1,
                semantic_score=round(tech_score1 * 0.95, 1),
                experience_score=round(min(100.0, (cand.total_experience_years / 5.0) * 90), 1),
                education_score=90.0,
                explanation={
                    "summary": f"{cand.name} matches {len(matched_j1)} of {len(job1_reqs)} key requirements for {job1.title}.",
                    "interview_questions": [f"Describe your production experience with {matched_j1[0]}." if matched_j1 else "Describe your software architecture background."],
                    "recruiter_insights": [f"Candidate possesses {cand.total_experience_years} years of demonstrated experience."]
                },
                strengths=[f"Strong proficiency in {s}" for s in matched_j1[:3]],
                skill_gaps=[f"Missing required background in {s}" for s in missing_j1[:3]],
                matched_skills=[{"skill": s, "type": "language"} for s in matched_j1],
                missing_skills=missing_j1[:5],
                related_skills=[]
            )
            db.add(analysis1)

            j2_reqs_lower = {r[0].lower() for r in job2_reqs}
            matched_j2 = [s for s in c_info["skills"] if s.lower() in j2_reqs_lower]
            missing_j2 = [r[0] for r in job2_reqs if r[0].lower() not in cand_skill_set]
            skill_ratio2 = len(matched_j2) / max(len(job2_reqs), 1)
            tech_score2 = round(min(100.0, skill_ratio2 * 100), 1)
            overall2 = round(tech_score2 * 0.5 + min(100.0, (cand.total_experience_years / 5.0) * 80) * 0.3 + 18.0, 1)

            analysis2 = MatchingAnalysis(
                job_id=job2.id,
                candidate_id=cand.id,
                user_id=recruiter.id,
                overall_score=overall2,
                technical_score=tech_score2,
                semantic_score=round(tech_score2 * 0.95, 1),
                experience_score=round(min(100.0, (cand.total_experience_years / 5.0) * 90), 1),
                education_score=95.0,
                explanation={
                    "summary": f"{cand.name} matches {len(matched_j2)} of {len(job2_reqs)} key requirements for {job2.title}.",
                    "interview_questions": [f"Describe your deep learning workflow using {matched_j2[0]}." if matched_j2 else "Describe your ML model serving experience."],
                    "recruiter_insights": [f"Candidate has {cand.total_experience_years} years in relevant domains."]
                },
                strengths=[f"Demonstrated domain mastery in {s}" for s in matched_j2[:3]],
                skill_gaps=[f"Missing experience in {s}" for s in missing_j2[:3]],
                matched_skills=[{"skill": s, "type": "ai_ml"} for s in matched_j2],
                missing_skills=missing_j2[:5],
                related_skills=[]
            )
            db.add(analysis2)
        else:
            # Match against Job 1
            m1 = matching_engine.match(
                job_data=job1_data,
                candidate_data={"name": cand.name, "total_experience_years": cand.total_experience_years, "education": cand.education},
                candidate_skills=c_info["skills"],
                resume_text=res.raw_text
            )

            q1 = question_gen.generate_questions(
                job_title=job1.title,
                matched_skills=[m["skill"] for m in m1["matched_skills"]],
                missing_skills=m1["missing_skills"],
                experience_years=cand.total_experience_years,
                candidate_projects=cand.extracted_profile.get("projects", [])
            )

            i1 = insights_gen.generate_insights(
                candidate_name=cand.name,
                overall_score=m1["overall_score"],
                matched_skills=m1["matched_skills"],
                missing_skills=m1["missing_skills"],
                experience_years=cand.total_experience_years,
                min_experience_required=job1.min_experience
            )

            m1["explanation"]["interview_questions"] = q1
            m1["explanation"]["recruiter_insights"] = i1

            analysis1 = MatchingAnalysis(
                job_id=job1.id,
                candidate_id=cand.id,
                user_id=recruiter.id,
                overall_score=m1["overall_score"],
                technical_score=m1["technical_score"],
                semantic_score=m1["semantic_score"],
                experience_score=m1["experience_score"],
                education_score=m1["education_score"],
                explanation=m1["explanation"],
                strengths=m1["strengths"],
                skill_gaps=m1["skill_gaps"],
                matched_skills=m1["matched_skills"],
                missing_skills=m1["missing_skills"],
                related_skills=m1["related_skills"]
            )
            db.add(analysis1)

            # Match against Job 2
            m2 = matching_engine.match(
                job_data=job2_data,
                candidate_data={"name": cand.name, "total_experience_years": cand.total_experience_years, "education": cand.education},
                candidate_skills=c_info["skills"],
                resume_text=res.raw_text
            )

            analysis2 = MatchingAnalysis(
                job_id=job2.id,
                candidate_id=cand.id,
                user_id=recruiter.id,
                overall_score=m2["overall_score"],
                technical_score=m2["technical_score"],
                semantic_score=m2["semantic_score"],
                experience_score=m2["experience_score"],
                education_score=m2["education_score"],
                explanation=m2["explanation"],
                strengths=m2["strengths"],
                skill_gaps=m2["skill_gaps"],
                matched_skills=m2["matched_skills"],
                missing_skills=m2["missing_skills"],
                related_skills=m2["related_skills"]
            )
            db.add(analysis2)

        # Shortlist the top 2 candidates for Job 1
        if idx in [0, 9]:
            db.add(Shortlist(
                job_id=job1.id,
                candidate_id=cand.id,
                user_id=recruiter.id,
                status="shortlisted",
                comments=f"Exemplary background in {job1.title}. High scoring candidate."
            ))

    # Activity log & initial notifications
    db.add(Notification(
        user_id=recruiter.id,
        type="success",
        title="System Initialized",
        message="TalentMatch AI platform successfully initialized with verified demo data.",
        is_read=False
    ))
    db.add(Notification(
        user_id=recruiter.id,
        type="info",
        title="12 Resumes Analyzed",
        message="Candidate pool ranked across Senior Full-Stack Engineer and Lead AI/NLP roles.",
        is_read=False
    ))
    db.add(ActivityLog(
        user_id=recruiter.id,
        action="SYSTEM_INIT",
        entity_type="system",
        entity_id="init-001",
        details={"status": "ready", "candidates_seeded": 12, "jobs_seeded": 2}
    ))

    db.commit()
    logger.info("Database seeding successfully completed.")

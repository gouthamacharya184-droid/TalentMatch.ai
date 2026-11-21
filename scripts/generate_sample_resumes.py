import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document

RESUMES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sample_resumes"))
JOBS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../sample_jobs"))
os.makedirs(RESUMES_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

CANDIDATES = [
    {
        "filename": "Alex_Chen_Senior_FullStack.pdf",
        "format": "pdf",
        "name": "Alex Chen",
        "title": "Senior Full-Stack Architect",
        "email": "alex.chen@example.com",
        "phone": "+1 (555) 234-5678",
        "location": "San Francisco, CA",
        "summary": "Accomplished Senior Full-Stack Architect with 8+ years of enterprise experience building scalable web applications and distributed microservices. Specialized in Python, FastAPI, React, and TypeScript.",
        "skills": "Python, FastAPI, Django, React, TypeScript, PostgreSQL, Docker, AWS, Redis, GraphQL, CI/CD, Git, Kubernetes, Tailwind CSS",
        "experience": [
            "Lead Software Architect at CloudScale Tech (2021 - Present, 3.5 yrs): Architected multi-tenant SaaS platform using FastAPI, React 18, and PostgreSQL. Reduced query latency by 45% using Redis caching and partitioned database indexing.",
            "Senior Full-Stack Engineer at Nexus Solutions (2018 - 2021, 3.0 yrs): Built high-throughput microservices using Python and Docker on AWS ECS. Mentored team of 6 engineers and established CI/CD deployment pipelines.",
            "Software Engineer at WebCraft Systems (2016 - 2018, 2.0 yrs): Developed responsive frontends with React and TypeScript, integrating with Python REST APIs."
        ],
        "education": "Master of Science in Computer Science, Stanford University (2016)"
    },
    {
        "filename": "Priya_Sharma_Lead_AI_NLP.pdf",
        "format": "pdf",
        "name": "Priya Sharma",
        "title": "Senior AI & NLP Engineer",
        "email": "priya.sharma@example.com",
        "phone": "+1 (555) 345-6789",
        "location": "New York, NY",
        "summary": "NLP and Applied AI specialist with 6+ years of expertise designing semantic search engines, transformer architectures, and LLM orchestration pipelines using Sentence Transformers, PyTorch, and FastAPI.",
        "skills": "Python, PyTorch, Transformers, Sentence Transformers, spaCy, FastAPI, Scikit-learn, Vector Databases, HuggingFace, Docker, AWS, Git",
        "experience": [
            "Staff AI Engineer at DeepSemantic AI (2022 - Present, 2.5 yrs): Designed vector similarity pipeline serving 10M+ daily semantic searches using Sentence Transformers and FAISS with sub-50ms latency.",
            "Senior NLP Researcher at LangTech Solutions (2019 - 2022, 3.0 yrs): Developed custom named entity recognition (NER) models with spaCy and fine-tuned BERT representations for biomedical information extraction.",
            "Machine Learning Engineer at DataVibe (2018 - 2019, 1.0 yr): Built text classification and sentiment models using Scikit-learn and PyTorch."
        ],
        "education": "Master of Science in Artificial Intelligence, Carnegie Mellon University (2018)"
    },
    {
        "filename": "Marcus_Vance_Senior_Backend.pdf",
        "format": "pdf",
        "name": "Marcus Vance",
        "title": "Senior Backend & Distributed Systems Engineer",
        "email": "marcus.vance@example.com",
        "phone": "+1 (555) 456-7890",
        "location": "Austin, TX",
        "summary": "Seasoned Backend Engineer with 5+ years of robust experience in Python, FastAPI, Django, PostgreSQL, and event-driven architectures. Passionate about database optimization and asynchronous worker processing.",
        "skills": "Python, FastAPI, Django, PostgreSQL, Redis, Celery, Docker, Kubernetes, AWS, SQL, REST APIs, Microservices, Git",
        "experience": [
            "Senior Backend Engineer at Apex Financial (2021 - Present, 3.0 yrs): Built mission-critical payment settlement engine processing $12M daily using FastAPI and PostgreSQL. Implemented asynchronous task queue using Celery and Redis.",
            "Backend Developer at Streamline Data (2019 - 2021, 2.0 yrs): Developed RESTful API endpoints and designed relational database schemas in PostgreSQL."
        ],
        "education": "Bachelor of Science in Computer Engineering, University of Texas at Austin (2019)"
    },
    {
        "filename": "Elena_Rostova_Frontend_Specialist.pdf",
        "format": "pdf",
        "name": "Elena Rostova",
        "title": "Senior Frontend Developer",
        "email": "elena.rostova@example.com",
        "phone": "+1 (555) 567-8901",
        "location": "Seattle, WA",
        "summary": "Creative and analytical Frontend Developer with 4+ years of expertise in React, TypeScript, Next.js, and modern CSS architecture. Focused on high-performance web applications and accessibility.",
        "skills": "React, TypeScript, Next.js, Tailwind CSS, Redux Toolkit, HTML5, CSS3, JavaScript, Jest, Webpack, Vite, Git",
        "experience": [
            "Senior Frontend Engineer at Horizon Web (2022 - Present, 2.0 yrs): Led design system implementation in React 18, TypeScript, and Tailwind CSS. Improved Lighthouse performance scores from 64 to 98.",
            "Frontend Engineer at Pulse Creative (2020 - 2022, 2.0 yrs): Built complex interactive data dashboards using React, Recharts, and TypeScript."
        ],
        "education": "Bachelor of Science in Software Engineering, University of Washington (2020)"
    },
    {
        "filename": "David_Kim_DevOps_Architect.pdf",
        "format": "pdf",
        "name": "David Kim",
        "title": "Cloud & DevOps Architect",
        "email": "david.kim@example.com",
        "phone": "+1 (555) 678-9012",
        "location": "Chicago, IL",
        "summary": "DevOps Architect with 7+ years of experience delivering automated CI/CD pipelines, container orchestration with Kubernetes, and Infrastructure as Code using Terraform across AWS and GCP environments.",
        "skills": "AWS, Kubernetes, Terraform, Docker, Python, CI/CD, Helm, Prometheus, Grafana, Linux, Bash, PostgreSQL, Git",
        "experience": [
            "Lead DevOps Engineer at CloudSphere (2020 - Present, 4.0 yrs): Designed multi-region EKS Kubernetes clusters and codified infrastructure with Terraform. Reduced deployment time by 80%.",
            "Site Reliability Engineer at MetricLabs (2017 - 2020, 3.0 yrs): Automated CI/CD build and release workflows with GitHub Actions and Docker. Built observability stack with Prometheus and Grafana."
        ],
        "education": "Bachelor of Science in Computer Science, University of Illinois Urbana-Champaign (2017)"
    },
    {
        "filename": "Samantha_Miller_FullStack_Dev.pdf",
        "format": "pdf",
        "name": "Samantha Miller",
        "title": "Full-Stack Software Engineer",
        "email": "samantha.miller@example.com",
        "phone": "+1 (555) 789-0123",
        "location": "Boston, MA",
        "summary": "Versatile Full-Stack Engineer with 3.5 years of experience developing modern web applications with React, TypeScript, Node.js, Python, and PostgreSQL.",
        "skills": "React, TypeScript, Python, Node.js, PostgreSQL, Docker, REST APIs, Git, Tailwind CSS, Express",
        "experience": [
            "Full-Stack Engineer at Beacon Digital (2022 - Present, 2.5 yrs): Developed enterprise collaboration tools using React and Python REST backend. Integrated PostgreSQL database models and unit testing suites.",
            "Junior Web Developer at TechForward (2021 - 2022, 1.0 yr): Maintained client-facing portals and built automated data synchronization scripts in Python."
        ],
        "education": "Bachelor of Science in Computer Science, Boston University (2021)"
    },
    {
        "filename": "Liam_OConnor_ML_Engineer.pdf",
        "format": "pdf",
        "name": "Liam O'Connor",
        "title": "Machine Learning Engineer",
        "email": "liam.oconnor@example.com",
        "phone": "+1 (555) 890-1234",
        "location": "Denver, CO",
        "summary": "Machine Learning Engineer with 4 years of industry experience training, evaluating, and deploying statistical models and deep neural networks in production using Scikit-learn, PyTorch, and Docker.",
        "skills": "Python, Scikit-learn, PyTorch, TensorFlow, Pandas, NumPy, SQL, Docker, FastAPI, MLflow, Git",
        "experience": [
            "ML Engineer at PredictiveAI (2022 - Present, 2.0 yrs): Deployed predictive classification models into production via FastAPI microservices on AWS EC2.",
            "Data Scientist at QuantAnalytics (2020 - 2022, 2.0 yrs): Developed statistical forecasting models and automated feature engineering pipelines."
        ],
        "education": "Master of Science in Data Science, University of Colorado Boulder (2020)"
    },
    {
        "filename": "Aaliyah_Patel_Data_Engineer.pdf",
        "format": "pdf",
        "name": "Aaliyah Patel",
        "title": "Senior Data Platform Engineer",
        "email": "aaliyah.patel@example.com",
        "phone": "+1 (555) 901-2345",
        "location": "Atlanta, GA",
        "summary": "Data Platform Engineer with 5 years of experience building scalable ETL/ELT data pipelines, data warehouses, and analytics infrastructure with Python, SQL, PostgreSQL, Apache Spark, and Airflow.",
        "skills": "Python, SQL, PostgreSQL, Apache Spark, Airflow, BigQuery, AWS, Docker, Kafka, Git",
        "experience": [
            "Senior Data Engineer at Synapse Data (2021 - Present, 3.0 yrs): Built automated data pipelines ingesting 5TB daily into PostgreSQL and Snowflake using Apache Airflow and Spark.",
            "Data Engineer at Logistics Core (2019 - 2021, 2.0 yrs): Maintained relational data warehouses and optimized complex SQL reporting queries."
        ],
        "education": "Bachelor of Science in Computer Engineering, Georgia Tech (2019)"
    },
    {
        "filename": "Daniel_Jackson_Junior_Dev.pdf",
        "format": "pdf",
        "name": "Daniel Jackson",
        "title": "Associate Software Engineer",
        "email": "daniel.jackson@example.com",
        "phone": "+1 (555) 012-3456",
        "location": "Raleigh, NC",
        "summary": "Eager and fast-learning Junior Software Developer with 1 year of hands-on experience building web interfaces with React, JavaScript, HTML, CSS, and basic Python scripting.",
        "skills": "JavaScript, React, Python, HTML5, CSS3, Git, SQLite, Node.js",
        "experience": [
            "Junior Web Developer at Apex Media (2023 - Present, 1.0 yr): Built responsive landing pages with React and supported internal dashboard bug fixes and feature tickets."
        ],
        "education": "Bachelor of Science in Information Systems, NC State University (2023)"
    },
    {
        "filename": "Sophia_Martinez_FullStack_Product.pdf",
        "format": "pdf",
        "name": "Sophia Martinez",
        "title": "Product-Minded Full-Stack Developer",
        "email": "sophia.martinez@example.com",
        "phone": "+1 (555) 123-4567",
        "location": "San Diego, CA",
        "summary": "Dynamic Full-Stack Developer with 4.5 years of experience designing, shipping, and maintaining user-centric applications using React, TypeScript, Python, FastAPI, and PostgreSQL.",
        "skills": "React, TypeScript, Python, FastAPI, PostgreSQL, Tailwind CSS, Docker, AWS, REST APIs, Git",
        "experience": [
            "Full-Stack Developer at Elevate SaaS (2021 - Present, 3.0 yrs): Architected responsive React user interface and Python FastAPI backend for customer analytics portal.",
            "Frontend Engineer at Nova Interactive (2019 - 2021, 1.5 yrs): Built reusable UI components and collaborated with UX designers to deliver responsive web apps."
        ],
        "education": "Bachelor of Science in Computer Science, UC San Diego (2019)"
    },
    # DOCX Resumes
    {
        "filename": "James_Wilson_Senior_Python_Backend.docx",
        "format": "docx",
        "name": "James Wilson",
        "title": "Senior Python Backend Engineer",
        "email": "james.wilson@example.com",
        "phone": "+1 (555) 234-9876",
        "location": "Philadelphia, PA",
        "summary": "Senior Python Backend Engineer with 6 years of expertise building scalable microservices with FastAPI, Django, PostgreSQL, Docker, and Redis.",
        "skills": "Python, FastAPI, Django, PostgreSQL, Docker, Redis, Celery, AWS, REST APIs, Git, Microservices",
        "experience": [
            "Senior Backend Engineer at CoreScale Systems (2021 - Present, 3.0 yrs): Engineered high-concurrency RESTful APIs in FastAPI, optimized PostgreSQL queries, and deployed services via Docker on AWS ECS.",
            "Software Developer at Keystone Financial (2018 - 2021, 3.0 yrs): Developed transactional backend services in Python and managed relational database schemas."
        ],
        "education": "Bachelor of Science in Computer Science, Penn State University (2018)"
    },
    {
        "filename": "Chloe_Tremblay_Frontend_Engineer.docx",
        "format": "docx",
        "name": "Chloe Tremblay",
        "title": "Frontend Engineer",
        "email": "chloe.tremblay@example.com",
        "phone": "+1 (555) 345-0987",
        "location": "Montreal, QC",
        "summary": "Creative Frontend Engineer with 3 years of experience crafting interactive user interfaces using React, TypeScript, Vue.js, and Tailwind CSS.",
        "skills": "React, TypeScript, Vue.js, Tailwind CSS, JavaScript, HTML5, CSS3, Redux, Git",
        "experience": [
            "Frontend Developer at StudioVeloce (2022 - Present, 2.0 yrs): Built accessible web interfaces and state-managed dashboards using React, TypeScript, and modern styling libraries.",
            "Junior Web Developer at PixelNorth (2021 - 2022, 1.0 yr): Maintained frontend applications and integrated third-party REST APIs."
        ],
        "education": "Bachelor of Software Engineering, McGill University (2021)"
    },
    {
        "filename": "Rohan_Gupta_NLP_Researcher.docx",
        "format": "docx",
        "name": "Rohan Gupta",
        "title": "Applied NLP Scientist",
        "email": "rohan.gupta@example.com",
        "phone": "+1 (555) 456-1098",
        "location": "Toronto, ON",
        "summary": "NLP Scientist with 4 years of experience applying Sentence Transformers, spaCy, and PyTorch to text categorization, semantic search, and document entity linking.",
        "skills": "Python, spaCy, Sentence Transformers, PyTorch, Hugging Face, Scikit-learn, FastAPI, Docker, SQL, Git",
        "experience": [
            "NLP Engineer at CogniSemantic (2022 - Present, 2.0 yrs): Built semantic matching algorithms using all-MiniLM-L6-v2 embeddings and cosine similarity scoring for document ranking.",
            "Data Scientist at VectorLabs (2020 - 2022, 2.0 yrs): Trained text classification pipelines and topic modeling using Scikit-learn and spaCy."
        ],
        "education": "Master of Science in Computer Science, University of Toronto (2020)"
    },
    {
        "filename": "Carlos_Rivera_Infra_Engineer.docx",
        "format": "docx",
        "name": "Carlos Rivera",
        "title": "Senior Infrastructure & Cloud Engineer",
        "email": "carlos.rivera@example.com",
        "phone": "+1 (555) 567-2109",
        "location": "Phoenix, AZ",
        "summary": "Senior Infrastructure Engineer with 6.5 years of experience automating cloud infrastructure with Terraform, Docker, Kubernetes, and AWS.",
        "skills": "Terraform, AWS, Docker, Kubernetes, Linux, Python, CI/CD, Ansible, Bash, PostgreSQL, Git",
        "experience": [
            "Lead Cloud Infrastructure Engineer at SolTerra (2020 - Present, 4.0 yrs): Built multi-account AWS architecture via Terraform. Deployed containerized applications with Docker and Kubernetes.",
            "DevOps Engineer at SkyPulse (2017 - 2020, 2.5 yrs): Managed CI/CD pipelines and automated server provisioning with Python scripts and Ansible."
        ],
        "education": "Bachelor of Science in Computer Systems, Arizona State University (2017)"
    },
    {
        "filename": "Nina_Kowalska_FullStack_Web.docx",
        "format": "docx",
        "name": "Nina Kowalska",
        "title": "Full-Stack Web Developer",
        "email": "nina.kowalska@example.com",
        "phone": "+1 (555) 678-3210",
        "location": "Minneapolis, MN",
        "summary": "Full-Stack Developer with 3 years of experience engineering web apps using React, TypeScript, Python, Flask, and PostgreSQL.",
        "skills": "React, TypeScript, Python, Flask, PostgreSQL, Docker, HTML5, CSS3, REST APIs, Git",
        "experience": [
            "Full-Stack Developer at NorthStar Apps (2022 - Present, 2.0 yrs): Engineered full-stack features using React with TypeScript on frontend and Python Flask on backend.",
            "Junior Developer at Lakefront Media (2021 - 2022, 1.0 yr): Maintained frontend bug fixes and wrote relational PostgreSQL database queries."
        ],
        "education": "Bachelor of Science in Computer Science, University of Minnesota (2021)"
    }
]

def generate_pdf(c, path):
    doc = SimpleDocTemplate(path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor='#1e3a8a',
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor='#2563eb',
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    contact_style = ParagraphStyle(
        'DocContact',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor='#475569',
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor='#1e293b',
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor='#334155',
        spaceAfter=4
    )

    story = [
        Paragraph(c['name'], title_style),
        Paragraph(c['title'], subtitle_style),
        Paragraph(f"{c['email']} &nbsp;|&nbsp; {c['phone']} &nbsp;|&nbsp; {c['location']}", contact_style),
        Spacer(1, 4),
        Paragraph("PROFESSIONAL SUMMARY", heading_style),
        Paragraph(c['summary'], body_style),
        Spacer(1, 4),
        Paragraph("TECHNICAL SKILLS", heading_style),
        Paragraph(c['skills'], body_style),
        Spacer(1, 4),
        Paragraph("PROFESSIONAL EXPERIENCE", heading_style),
    ]

    for exp in c['experience']:
        story.append(Paragraph(f"• {exp}", body_style))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 4))
    story.append(Paragraph("EDUCATION", heading_style))
    story.append(Paragraph(c['education'], body_style))

    doc.build(story)


def generate_docx(c, path):
    doc = Document()
    doc.add_heading(c['name'], level=0)
    p_sub = doc.add_paragraph()
    p_sub.add_run(c['title']).bold = True
    
    p_contact = doc.add_paragraph(f"{c['email']} | {c['phone']} | {c['location']}")
    
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(c['summary'])
    
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph(c['skills'])
    
    doc.add_heading("Professional Experience", level=1)
    for exp in c['experience']:
        doc.add_paragraph(exp, style='List Bullet')
        
    doc.add_heading("Education", level=1)
    doc.add_paragraph(c['education'])
    
    doc.save(path)


def main():
    print("Generating 15 candidate resumes (10 PDF, 5 DOCX)...")
    for c in CANDIDATES:
        out_path = os.path.join(RESUMES_DIR, c['filename'])
        if c['format'] == 'pdf':
            generate_pdf(c, out_path)
        else:
            generate_docx(c, out_path)
        print(f"Created: {c['filename']}")

    # Generate Sample Jobs
    jobs = [
        {
            "filename_base": "Job_Senior_FullStack_Engineer",
            "title": "Senior Full-Stack Engineer",
            "company": "AVOM Consultants",
            "location": "Remote (US / Global)",
            "min_experience": "4.0",
            "education": "Bachelor's Degree in Computer Science or related",
            "description": """Job Title: Senior Full-Stack Engineer
Company: AVOM Consultants
Location: Remote
Employment Type: Full-time
Minimum Experience: 4 years
Education Requirement: Bachelor's Degree in Computer Science or related field

Job Overview:
We are seeking an experienced Senior Full-Stack Engineer to architect and build high-performance web applications for our enterprise SaaS recruitment platform.
You will work with modern technologies including Python (FastAPI), React, TypeScript, and PostgreSQL.

Key Responsibilities:
- Design and develop scalable RESTful APIs with Python and FastAPI.
- Build responsive, accessible, and high-performance UI components using React and TypeScript.
- Architect relational database models and optimize queries in PostgreSQL.
- Containerize services with Docker and manage deployment pipelines.
- Integrate automated testing and CI/CD workflows.

Required Technical Skills:
- Python
- FastAPI
- React
- TypeScript
- PostgreSQL
- Docker
- REST APIs

Preferred Qualifications:
- Redis caching
- AWS Cloud deployment
- Tailwind CSS
- Kubernetes container orchestration
"""
        },
        {
            "filename_base": "Job_Lead_AI_NLP_Engineer",
            "title": "Lead AI & NLP Engineer",
            "company": "Cognitive Systems Labs",
            "location": "San Francisco, CA / Hybrid",
            "min_experience": "5.0",
            "education": "Master's Degree in Computer Science or AI/ML",
            "description": """Job Title: Lead AI & NLP Engineer
Company: Cognitive Systems Labs
Location: San Francisco, CA / Hybrid
Employment Type: Full-time
Minimum Experience: 5 years
Education Requirement: Master's Degree in Computer Science or AI/ML

Job Overview:
Join our advanced AI team to build semantic resume matching algorithms, vector embeddings, and LLM applications.

Key Responsibilities:
- Develop NLP pipelines using spaCy, Hugging Face Transformers, and Sentence Transformers.
- Design vector similarity search pipelines using cosine similarity and vector databases.
- Deploy scalable AI inference microservices with FastAPI and Docker.
- Implement explainable AI scoring systems and evaluate ranking accuracy.

Required Skills:
- Python
- PyTorch or TensorFlow
- Sentence Transformers
- spaCy
- Scikit-learn
- FastAPI
- Docker

Preferred Skills:
- Vector Databases
- AWS / GCP MLOps
- LangChain / RAG architectures
"""
        }
    ]

    print("\nGenerating sample job descriptions (PDF, DOCX, TXT)...")
    for j in jobs:
        # TXT
        txt_path = os.path.join(JOBS_DIR, f"{j['filename_base']}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(j['description'])
        print(f"Created: {j['filename_base']}.txt")

        # PDF
        pdf_path = os.path.join(JOBS_DIR, f"{j['filename_base']}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(j['title'], styles['Heading1']),
            Paragraph(f"<b>Company:</b> {j['company']} | <b>Location:</b> {j['location']} | <b>Min Experience:</b> {j['min_experience']} yrs", styles['Normal']),
            Spacer(1, 10)
        ]
        for line in j['description'].split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), styles['Normal']))
                story.append(Spacer(1, 4))
        doc.build(story)
        print(f"Created: {j['filename_base']}.pdf")

        # DOCX
        docx_path = os.path.join(JOBS_DIR, f"{j['filename_base']}.docx")
        doc_docx = Document()
        doc_docx.add_heading(j['title'], level=0)
        doc_docx.add_paragraph(f"Company: {j['company']} | Location: {j['location']} | Min Experience: {j['min_experience']} yrs")
        for line in j['description'].split("\n"):
            if line.strip():
                doc_docx.add_paragraph(line.strip())
        doc_docx.save(docx_path)
        print(f"Created: {j['filename_base']}.docx")

    print("\nAll sample resumes and job documents generated successfully!")

if __name__ == "__main__":
    main()


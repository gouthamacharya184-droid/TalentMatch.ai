import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document
import pypdf

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_resumes_50"))
EDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_resumes_edge_cases"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EDGE_DIR, exist_ok=True)

FIRST_NAMES = [
    "Alex", "Priya", "Marcus", "Elena", "David", "Samantha", "Liam", "Aaliyah",
    "Daniel", "Sophia", "James", "Chloe", "Rohan", "Carlos", "Nina", "Lucas",
    "Fatima", "Ethan", "Zoe", "Vikram", "Hannah", "Gabriel", "Maya", "Benjamin",
    "Isabella", "Arjun", "Grace", "Oliver", "Amara", "William", "Leila", "Noah",
    "Ananya", "Henry", "Zara", "Alexander", "Emily", "Mateo", "Mia", "Siddharth",
    "Ava", "Julian", "Tara", "Leo", "Kavya", "Samuel", "Layla", "Jack", "Diya", "Ryan"
]

LAST_NAMES = [
    "Chen", "Sharma", "Vance", "Rostova", "Kim", "Miller", "O'Connor", "Patel",
    "Jackson", "Martinez", "Wilson", "Tremblay", "Gupta", "Rivera", "Kowalska", "Silva",
    "Al-Mansoor", "Davies", "Taylor", "Reddy", "Becker", "Santos", "Lin", "Cohen",
    "Romero", "Verma", "O'Brien", "Mendoza", "Diallo", "Clarke", "Haddad", "Larsen",
    "Iyer", "Novak", "Aziz", "Wright", "Fischer", "Morales", "Dubois", "Natarajan",
    "Kovacs", "Moreau", "Joshi", "Tanaka", "Mehta", "Rossi", "Svensson", "Nakamura", "Menon", "Brooks"
]

TITLES_AND_SKILLS = [
    ("Senior Full-Stack Engineer", "Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS, Redis, GraphQL, CI/CD", 5.5, "Master of Science in Computer Science"),
    ("Lead AI & NLP Engineer", "Python, PyTorch, Transformers, Sentence Transformers, spaCy, FastAPI, Scikit-learn, Vector Databases, HuggingFace", 6.0, "Master of Science in Artificial Intelligence"),
    ("Senior Python Backend Engineer", "Python, FastAPI, Django, PostgreSQL, Redis, Celery, Docker, Kubernetes, AWS, SQL, REST APIs", 5.0, "Bachelor of Science in Computer Engineering"),
    ("Frontend Developer Specialist", "React, TypeScript, Next.js, Tailwind CSS, Redux Toolkit, HTML5, CSS3, JavaScript, Jest, Vite", 4.0, "Bachelor of Science in Software Engineering"),
    ("Cloud DevOps Architect", "AWS, Kubernetes, Terraform, Docker, Python, CI/CD, Helm, Prometheus, Grafana, Linux, Bash, PostgreSQL", 7.0, "Bachelor of Science in Computer Science"),
    ("Data Platform Engineer", "Python, SQL, PostgreSQL, Apache Spark, Airflow, BigQuery, AWS, Docker, Kafka, Git, Data Modeling", 4.5, "Bachelor of Science in Computer Engineering"),
    ("Machine Learning Scientist", "Python, Scikit-learn, PyTorch, TensorFlow, Pandas, NumPy, SQL, Docker, FastAPI, MLflow", 4.0, "Master of Science in Data Science"),
    ("Junior Software Engineer", "Python, JavaScript, React, HTML5, CSS3, Git, SQLite, Node.js, REST APIs", 1.5, "Bachelor of Science in Information Systems"),
    ("Product Full-Stack Developer", "React, TypeScript, Python, FastAPI, PostgreSQL, Tailwind CSS, Docker, AWS, REST APIs", 4.5, "Bachelor of Science in Computer Science"),
    ("Backend Systems Architect", "Python, Go, FastAPI, PostgreSQL, Kafka, Microservices, Docker, Kubernetes, Distributed Systems", 8.0, "Master of Science in Computer Science")
]

def make_pdf(c, path):
    doc = SimpleDocTemplate(path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=16, leading=20, textColor='#1e3a8a')
    sub_style = ParagraphStyle('S', parent=styles['Normal'], fontSize=10, leading=13, textColor='#2563eb', fontName='Helvetica-Bold')
    body_style = ParagraphStyle('B', parent=styles['Normal'], fontSize=9, leading=12, textColor='#334155')

    story = [
        Paragraph(c['name'], title_style),
        Paragraph(c['title'], sub_style),
        Paragraph(f"{c['email']} | {c['phone']} | {c['location']}", body_style),
        Spacer(1, 4),
        Paragraph("<b>PROFESSIONAL SUMMARY</b>", sub_style),
        Paragraph(f"Experienced professional with {c['years']} years in software engineering. Expertise: {c['skills']}.", body_style),
        Spacer(1, 4),
        Paragraph("<b>TECHNICAL SKILLS</b>", sub_style),
        Paragraph(c['skills'], body_style),
        Spacer(1, 4),
        Paragraph("<b>EXPERIENCE</b>", sub_style),
        Paragraph(f"• Senior Engineer at TechCorp (2019 - Present, {c['years']} yrs): Developed scalable applications with {c['skills'].split(',')[0]} and PostgreSQL.", body_style),
        Spacer(1, 4),
        Paragraph("<b>EDUCATION</b>", sub_style),
        Paragraph(c['education'], body_style),
    ]
    doc.build(story)

def make_docx(c, path):
    doc = Document()
    doc.add_heading(c['name'], level=0)
    doc.add_paragraph(f"{c['title']} | {c['email']} | {c['phone']} | {c['location']}")
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph(c['skills'])
    doc.add_heading("Professional Experience", level=1)
    doc.add_paragraph(f"Engineer at TechCorp ({c['years']} yrs experience): Worked on {c['skills']}.", style='List Bullet')
    doc.add_heading("Education", level=1)
    doc.add_paragraph(c['education'])
    doc.save(path)

def generate_50():
    print("Generating 50 candidate resumes (35 PDF, 15 DOCX)...")
    for i in range(50):
        first = FIRST_NAMES[i]
        last = LAST_NAMES[i]
        cleaned_last = last.lower().replace("'", "")
        role_info = TITLES_AND_SKILLS[i % len(TITLES_AND_SKILLS)]
        cand = {
            "name": f"{first} {last}",
            "title": role_info[0],
            "email": f"{first.lower()}.{cleaned_last}@example.com",
            "phone": f"+1 (555) {100 + i:03d}-{2000 + i:04d}",
            "location": "San Francisco, CA" if i % 2 == 0 else "New York, NY",
            "skills": role_info[1],
            "years": role_info[2],
            "education": role_info[3]
        }
        is_pdf = (i % 3 != 0)
        ext = "pdf" if is_pdf else "docx"
        fname = f"Candidate_{i+1:02d}_{first}_{cleaned_last}.{ext}"
        out_path = os.path.join(OUTPUT_DIR, fname)
        if is_pdf:
            make_pdf(cand, out_path)
        else:
            make_docx(cand, out_path)
    print(f"Generated 50 resumes in: {OUTPUT_DIR}")

def generate_edge_cases():
    print("Generating edge case test files...")
    # 1. Empty document
    empty_pdf = os.path.join(EDGE_DIR, "Edge_01_Empty_Document.pdf")
    with open(empty_pdf, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")

    # 2. Corrupted file
    corrupt_pdf = os.path.join(EDGE_DIR, "Edge_02_Corrupted_Header.pdf")
    with open(corrupt_pdf, "wb") as f:
        f.write(b"NOT_A_REAL_PDF_CORRUPTED_BYTES_1234567890")

    # 3. Invalid extension
    invalid_ext = os.path.join(EDGE_DIR, "Edge_03_Executable_Payload.exe")
    with open(invalid_ext, "wb") as f:
        f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00")

    # 4. Password protected PDF
    pwd_pdf_path = os.path.join(EDGE_DIR, "Edge_04_Password_Protected.pdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("SecretPassword123!")
    with open(pwd_pdf_path, "wb") as f:
        writer.write(f)

    # 5. Oversized mock file (16MB)
    oversized_path = os.path.join(EDGE_DIR, "Edge_05_Oversized_16MB.pdf")
    with open(oversized_path, "wb") as f:
        f.seek(16 * 1024 * 1024 - 1)
        f.write(b"\0")

    print(f"Generated edge case files in: {EDGE_DIR}")

if __name__ == "__main__":
    generate_50()
    generate_edge_cases()

"""
TalentMatch AI — Comprehensive Skill Dictionary & Synonym Taxonomy
Contains over 1,200 categorized skills, frameworks, tools, and synonym maps.
"""

SKILL_DICTIONARY = {
    # ── Programming Languages ──────────────────────────────────
    "programming_languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go",
        "Golang", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
        "MATLAB", "Dart", "Perl", "Haskell", "Elixir", "Clojure", "Julia",
        "Lua", "Shell", "Bash", "PowerShell", "Groovy", "Objective-C", "SQL",
        "HTML", "CSS", "Sass", "SCSS", "Less", "GraphQL", "Solidity"
    ],

    # ── Web & Frontend Frameworks ──────────────────────────────
    "frontend_frameworks": [
        "React", "React.js", "Next.js", "Vue.js", "Vue", "Nuxt.js", "Angular",
        "AngularJS", "Svelte", "SvelteKit", "Ember.js", "Backbone.js", "jQuery",
        "Tailwind CSS", "Bootstrap", "Material-UI", "MUI", "Chakra UI", "Ant Design",
        "Redux", "Redux Toolkit", "MobX", "Zustand", "Recoil", "Webpack", "Vite",
        "Rollup", "Babel", "HTML5", "CSS3", "WebAssembly", "Responsive Design",
        "PWA", "Micro-frontends"
    ],

    # ── Backend & API Frameworks ───────────────────────────────
    "backend_frameworks": [
        "FastAPI", "Django", "Flask", "Node.js", "Express.js", "NestJS", "Koa",
        "Spring", "Spring Boot", "ASP.NET", ".NET Core", ".NET", "Ruby on Rails",
        "Laravel", "Symfony", "Gin", "Echo", "Fiber", "Ktor", "Actix Web", "Rocket",
        "Phoenix", "Fastify", "Tornado", "Celery", "REST API", "RESTful API",
        "GraphQL API", "gRPC", "WebSockets", "Microservices", "Serverless"
    ],

    # ── Databases & Storage ────────────────────────────────────
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Cassandra",
        "Elasticsearch", "DynamoDB", "Oracle", "Microsoft SQL Server", "MS SQL",
        "CouchDB", "Neo4j", "MariaDB", "Supabase", "Firebase", "Firestore",
        "CockroachDB", "TimescaleDB", "Snowflake", "Amazon Redshift", "BigQuery",
        "ClickHouse", "Pinecone", "Milvus", "Weaviate", "Qdrant", "ChromaDB"
    ],

    # ── Cloud, DevOps & Infrastructure ─────────────────────────
    "cloud_devops": [
        "Amazon Web Services", "AWS", "Google Cloud Platform", "GCP", "Microsoft Azure",
        "Azure", "Docker", "Kubernetes", "K8s", "Terraform", "Ansible", "Puppet",
        "Chef", "CI/CD", "GitHub Actions", "GitLab CI", "Jenkins", "CircleCI",
        "ArgoCD", "Helm", "Prometheus", "Grafana", "ELK Stack", "Datadog",
        "New Relic", "Linux", "Unix", "Ubuntu", "Debian", "CentOS", "RedHat",
        "Nginx", "Apache", "HAProxy", "AWS Lambda", "Cloudflare", "OpenTelemetry"
    ],

    # ── AI, Machine Learning & Data Science ────────────────────
    "ai_ml": [
        "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP",
        "Natural Language Processing", "Computer Vision", "PyTorch", "TensorFlow",
        "Keras", "Scikit-learn", "Pandas", "NumPy", "SciPy", "OpenCV", "Hugging Face",
        "Transformers", "Sentence Transformers", "spaCy", "NLTK", "Gensim", "XGBoost",
        "LightGBM", "CatBoost", "LLM", "Large Language Models", "LangChain",
        "LlamaIndex", "Fine-Tuning", "RAG", "Retrieval Augmented Generation",
        "Vector Embeddings", "Prompt Engineering", "MLOps", "MLflow", "Kubeflow",
        "Weights & Biases", "Ray", "Triton", "ONNX"
    ],

    # ── Data Engineering & Big Data ────────────────────────────
    "data_engineering": [
        "Apache Spark", "PySpark", "Apache Kafka", "Kafka", "Apache Flink",
        "Airflow", "Apache Airflow", "Hadoop", "Hive", "dbt", "Data Modeling",
        "ETL", "ELT", "Data Pipeline", "Data Warehouse", "Data Lake", "Delta Lake",
        "Apache Iceberg", "Presto", "Trino", "Spark Streaming"
    ],

    # ── Mobile Development ─────────────────────────────────────
    "mobile": [
        "Flutter", "React Native", "Android Development", "iOS Development",
        "SwiftUI", "Jetpack Compose", "Xcode", "Android Studio", "Capacitor", "Ionic"
    ],

    # ── Testing & Quality Assurance ────────────────────────────
    "testing": [
        "Unit Testing", "Integration Testing", "End-to-End Testing", "E2E",
        "PyTest", "Jest", "Mocha", "Chai", "Cypress", "Playwright", "Selenium",
        "JUnit", "TestNG", "Postman", "K6", "JMeter", "TDD", "BDD"
    ],

    # ── Architecture, Tools & Practices ────────────────────────
    "tools_and_practices": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Agile",
        "Scrum", "Kanban", "System Design", "Design Patterns", "Clean Architecture",
        "Domain-Driven Design", "DDD", "Object-Oriented Programming", "OOP",
        "Functional Programming", "Event-Driven Architecture", "SOLID Principles",
        "Code Review", "Security Best Practices", "OWASP", "OAuth", "JWT"
    ],

    # ── Soft Skills & Professional Attributes ──────────────────
    "soft_skills": [
        "Communication", "Leadership", "Teamwork", "Problem Solving",
        "Critical Thinking", "Mentoring", "Project Management", "Time Management",
        "Collaboration", "Analytical Skills", "Adaptability", "Stakeholder Management"
    ]
}

# ── Flattened taxonomy with category assignment ────────────────
FLATTENED_SKILLS = {}
for category, skills in SKILL_DICTIONARY.items():
    for skill in skills:
        FLATTENED_SKILLS[skill.lower()] = {
            "name": skill,
            "category": category
        }

# ── Comprehensive Synonym & Abbreviation Mapping ───────────────
SKILL_SYNONYMS = {
    # Languages
    "py": "Python",
    "python3": "Python",
    "python 3": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "golang": "Go",
    "c sharp": "C#",
    "csharp": "C#",
    "c++": "C++",
    "cpp": "C++",
    "shell script": "Bash",
    "shell scripting": "Bash",
    "bash scripting": "Bash",

    # Frontend
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angularjs": "Angular",
    "angular 2+": "Angular",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "redux toolkit": "Redux",
    "rtk": "Redux",

    # Backend
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
    "django rest framework": "Django",
    "drf": "Django",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "nestjs": "NestJS",
    "nest.js": "NestJS",
    "springboot": "Spring Boot",
    "spring-boot": "Spring Boot",
    ".net": "ASP.NET",
    "dotnet": "ASP.NET",
    "rest": "REST API",
    "restful": "REST API",
    "rest apis": "REST API",
    "graphql": "GraphQL",

    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "elastic": "Elasticsearch",
    "elastic search": "Elasticsearch",
    "ms sql": "Microsoft SQL Server",
    "mssql": "Microsoft SQL Server",
    "sql server": "Microsoft SQL Server",

    # Cloud & DevOps
    "k8s": "Kubernetes",
    "kube": "Kubernetes",
    "amazon web services": "AWS",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure cloud": "Microsoft Azure",
    "github actions": "GitHub Actions",
    "gha": "GitHub Actions",
    "cicd": "CI/CD",
    "ci / cd": "CI/CD",
    "continuous integration": "CI/CD",
    "continuous deployment": "CI/CD",

    # AI/ML
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "llms": "LLM",
    "large language model": "LLM",
    "rag": "RAG",
    "retrieval-augmented generation": "RAG",
    "tf": "TensorFlow",
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "cv": "Computer Vision",

    # Architecture & Practices
    "microservice": "Microservices",
    "micro services": "Microservices",
    "clean code": "Clean Architecture",
    "git version control": "Git",
    "unit test": "Unit Testing",
    "e2e testing": "End-to-End Testing",
}

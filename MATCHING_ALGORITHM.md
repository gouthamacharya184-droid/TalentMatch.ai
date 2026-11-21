# MATCHING ALGORITHM SPECIFICATION & MATHEMATICAL FORMULATION

**Platform:** TalentMatch AI — Resume Matching & Candidate Ranking Platform  
**Implementation Source:** `backend/app/ai_engine/matching_engine.py`  
**Execution Context:** Production Deterministic AI Inference Engine  
**Version:** 1.0.0  

---

## 1. Algorithm Overview

TalentMatch AI uses a transparent, explainable 4-component weighted scoring formula to compute an overall compatibility score between 0.0 and 100.0 points.

Unlike black-box LLM scoring or naive keyword counters, every point in TalentMatch AI is grounded in extracted resume evidence, cosine semantic vectors, and verified career metrics.

$$\mathbf{S_{\text{overall}}} = \mathbf{S_{\text{tech}}} + \mathbf{S_{\text{semantic}}} + \mathbf{S_{\text{exp}}} + \mathbf{S_{\text{edu}}}$$

| Component | Weight | Max Points | Core Technology |
| :--- | :---: | :---: | :--- |
| **1. Technical Skills Match** ($S_{\text{tech}}$) | 40% | 40.0 pts | NLP Taxonomy & Synonym Matcher (1,200+ skills) |
| **2. Semantic Similarity** ($S_{\text{semantic}}$) | 30% | 30.0 pts | Sentence Transformers (`all-MiniLM-L6-v2`) Cosine Sim |
| **3. Relevant Experience** ($S_{\text{exp}}$) | 20% | 20.0 pts | Non-overlapping Date Duration vs. Job Minimum |
| **4. Education & Qualifications** ($S_{\text{edu}}$) | 10% | 10.0 pts | Degree Hierarchy Alignment |
| **Total** | **100%** | **100.0 pts** | **Explainable Hybrid Score** |

---

## 2. Component Mathematical Formulations

### Component 1: Technical Skills Match (Max: 40.0 Points)

Job requirements are partitioned into **Mandatory** ($M$) and **Preferred** ($P$) requirements.
Mandatory requirements carry double weight ($w_m = 2.0$) compared to preferred requirements ($w_p = 1.0$).

The total available weight is:
$$W_{\text{total}} = 2 \cdot |M| + 1 \cdot |P|$$

For each mandatory skill requirement $m \in M$:
- **Exact Match:** If $m \in \text{Candidate Skills}$, earned points $E_m = 2.0$ (Confidence: 0.98).
- **Related / Partial Match:** If $m$ has a substring or synonym match in candidate skills, $E_m = 1.2$ (Confidence: 0.75).
- **Missing:** If neither, $E_m = 0.0$.

For each preferred skill requirement $p \in P$:
- **Exact Match:** Earned points $E_p = 1.0$ (Confidence: 0.95).
- **Related / Partial Match:** Earned points $E_p = 0.6$ (Confidence: 0.70).
- **Missing:** $E_p = 0.0$.

The technical score is computed as:
$$S_{\text{tech}} = \min\left(40.0, \, \frac{\sum_{m \in M} E_m + \sum_{p \in P} E_p}{W_{\text{total}}} \times 40.0\right)$$

---

### Component 2: Semantic Similarity (Max: 30.0 Points)

To capture contextual relevance beyond exact keywords (e.g. distributed systems, API architecture, event-driven design), the engine computes dense embeddings using `all-MiniLM-L6-v2`:

1. **Job Semantic Document:** Target job title and description text.
2. **Candidate Semantic Document:** Profile summary, verified career duration, skills list, and resume body text. Protected demographic markers (name, phone, email) are omitted to prevent bias.
3. **Embeddings:** 384-dimensional unit vectors $\mathbf{u}, \mathbf{v} \in \mathbb{R}^{384}$.
4. **Cosine Similarity:**
   $$\text{sim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
5. Normalized to $[0.0, 1.0]$:
   $$\text{sim}_{\text{norm}} = \max\left(0.0, \, \min\left(1.0, \, \frac{\text{sim} + 1.0}{2.0}\right)\right)$$
6. The semantic score is:
   $$S_{\text{semantic}} = \text{sim}_{\text{norm}} \times 30.0$$

*Fallback:* If PyTorch / Sentence Transformers is unavailable, a Scikit-Learn TF-IDF N-gram vectorizer computes cosine similarity deterministically.

---

### Component 3: Relevant Experience (Max: 20.0 Points)

Candidate experience duration is calculated by merging overlapping employment dates to avoid double-counting concurrent roles:

$$\text{Exp}_{\text{cand}} = \text{Total verified non-overlapping years of experience}$$
$$\text{Exp}_{\text{req}} = \text{Minimum years of experience required by job}$$

1. If $\text{Exp}_{\text{req}} \le 0$:
   $$S_{\text{exp}} = 20.0$$
2. If candidate meets or exceeds the requirement ($\text{Exp}_{\text{cand}} \ge \text{Exp}_{\text{req}}$):
   $$R = \min\left(1.5, \, \frac{\text{Exp}_{\text{cand}}}{\text{Exp}_{\text{req}}}\right)$$
   $$S_{\text{exp}} = \min\left(20.0, \, 18.0 + (R - 1.0) \times 4.0\right)$$
   *(Meeting the exact threshold earns 18.0 pts; surplus relevant experience awards up to 20.0 pts)*
3. If candidate is below the required threshold ($\text{Exp}_{\text{cand}} < \text{Exp}_{\text{req}}$):
   $$S_{\text{exp}} = \max\left(4.0, \, \frac{\text{Exp}_{\text{cand}}}{\text{Exp}_{\text{req}}} \times 20.0\right)$$

---

### Component 4: Education & Qualifications (Max: 10.0 Points)

Candidate education credentials are evaluated against the target role criteria:

| Candidate Qualification | When Job Requires Bachelor's | When Job Requires Master's / Ph.D. |
| :--- | :---: | :---: |
| **Ph.D. / Doctorate** | 10.0 pts | 10.0 pts |
| **Master's Degree (M.S., M.Tech, MBA)** | 10.0 pts | 10.0 pts |
| **Bachelor's Degree (B.S., B.Tech, B.E.)** | 10.0 pts | 8.5 pts |
| **Associate's Degree / Diploma** | 7.5 pts | 7.5 pts |
| **Not specified in resume** | 6.0 pts | 6.0 pts |

*Missing education is never assigned 0 points or penalized harshly, but receives a transparent baseline of 6.0 points.*

---

## 3. Worked Example with Synthetic Candidate Data

### Target Job: Senior Full-Stack Engineer
- **Minimum Experience:** 4.0 Years
- **Education Requirement:** Bachelor's Degree in Computer Science
- **Mandatory Skills (5):** Python, React, PostgreSQL, Docker, FastAPI
- **Preferred Skills (3):** Redis, Kubernetes, AWS

### Candidate Profile: Alex Chen
- **Verified Experience:** 6.0 Years (Senior Full-Stack Developer)
- **Education:** Bachelor of Science in Computer Science, University of California (2018)
- **Extracted Skills:** Python, React, TypeScript, PostgreSQL, Docker, AWS, Git, Redis

### Calculation Walkthrough:

#### 1. Technical Skills ($S_{\text{tech}}$)
- **Mandatory Skills ($M$):**
  - Python $\to$ Matched exact ($+2.0$)
  - React $\to$ Matched exact ($+2.0$)
  - PostgreSQL $\to$ Matched exact ($+2.0$)
  - Docker $\to$ Matched exact ($+2.0$)
  - FastAPI $\to$ Missing ($0.0$)
- **Preferred Skills ($P$):**
  - Redis $\to$ Matched exact ($+1.0$)
  - AWS $\to$ Matched exact ($+1.0$)
  - Kubernetes $\to$ Missing ($0.0$)
- **Total Weights:** $2 \times 5 + 1 \times 3 = 13.0$
- **Earned Points:** $(2.0 \times 4) + (1.0 \times 2) = 10.0$
- **Score:**
  $$S_{\text{tech}} = \left(\frac{10.0}{13.0}\right) \times 40.0 = 30.77 \approx \mathbf{30.8 \text{ pts}}$$

#### 2. Semantic Similarity ($S_{\text{semantic}}$)
- SentenceTransformer cosine similarity between job document and Alex Chen profile document: $\text{sim} = 0.812$
- Normalized similarity: $\text{sim}_{\text{norm}} = 0.906$
- **Score:**
  $$S_{\text{semantic}} = 0.906 \times 30.0 = \mathbf{27.2 \text{ pts}}$$

#### 3. Relevant Experience ($S_{\text{exp}}$)
- Candidate Experience: $6.0$ yrs vs Required: $4.0$ yrs ($\text{Ratio} = 1.5$)
- **Score:**
  $$S_{\text{exp}} = 18.0 + (1.5 - 1.0) \times 4.0 = \mathbf{20.0 \text{ pts}}$$

#### 4. Education & Qualifications ($S_{\text{edu}}$)
- Target: Bachelor's Degree | Candidate: B.S. in Computer Science
- **Score:** $\mathbf{10.0 \text{ pts}}$

### Final Score Synthesis:
$$\mathbf{S_{\text{overall}}} = 30.8 + 27.2 + 20.0 + 10.0 = \mathbf{88.0\%}$$

### Output Explanation:
- **Verdict:** Highly Recommended (Tier 1 Match)
- **Strengths:** Strong technical match across 6 core skills; exceeds minimum experience (6.0 yrs vs 4.0 yrs required); verified B.S. degree.
- **Skill Gaps:** Missing mandatory skill `FastAPI`; missing preferred skill `Kubernetes`.

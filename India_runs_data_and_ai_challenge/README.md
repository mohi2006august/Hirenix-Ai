# HirenixAI — Intelligent Candidate Ranking System

![Dashboard Demo](https://placehold.co/800x400/1e1e2f/4a4a6a?text=HirenixAI+Dashboard)

An intelligent, context-aware candidate ranking engine built for the Redrob India Runs Data & AI Challenge. HirenixAI goes beyond simple keyword matching to deeply understand candidate experience, detect honeypot profiles, and leverage behavioral signals to produce a lightning-fast, highly accurate shortlist.

## 🚀 Key Features

*   **Honeypot Detection:** Identifies and rejects candidates who keyword-stuff AI skills but have no actual technical experience in their career history.
*   **Skill Trust Scoring:** Doesn't just check if a skill exists—weights it by proficiency level, number of endorsements, and months of duration.
*   **Semantic Understanding:** Uses `all-MiniLM-L6-v2` to embed a rich candidate document (combining weighted recent career history, education, and top skills) for semantic similarity matching against the Job Description.
*   **Deep Signal Integration:** Dynamically boosts scores based on education tiers, GitHub activity, skill assessment scores, and verification trust (email/phone/LinkedIn), while penalizing job-hopping and poor recruiter response rates.
*   **Fully Configurable:** A completely data-agnostic pipeline. Change the job description, required skills, and candidate data dynamically via the `job_config.json` or the web dashboard.
*   **Beautiful Web Dashboard:** A Flask + Vanilla JS/CSS dashboard featuring a glassmorphic config panel, dynamic pipeline counters, real-time pipeline execution, and detailed analytics.

---

## 🧠 System Architecture & Methodology

HirenixAI operates on a highly optimized, 3-stage funnel architecture designed to process massive talent pools rapidly while reserving computationally expensive operations for the most viable candidates.

### Stage 1: Heuristic Filtering & Honeypot Detection
*   **Goal:** Rapidly reduce the candidate pool by filtering out obvious misfits and trap profiles.
*   **Mechanism:**
    *   **Trap Rejection:** Immediately discards profiles with explicit reject titles (e.g., "HR Manager").
    *   **Honeypot Check:** Scans the candidate's entire career history descriptions. If they claim AI skills but their job descriptions contain zero technical keywords, they are rejected as honeypots.
    *   **Trust Scoring:** Calculates a base score using Title relevance + Skill Trust (Proficiency × Endorsements × Duration).

### Stage 2: Deep Semantic Matching
*   **Goal:** Understand the contextual fit of the candidate's actual experience against the nuanced requirements of the Job Description.
*   **Mechanism:**
    *   Uses the fast and efficient `SentenceTransformers` model (`all-MiniLM-L6-v2`).
    *   Constructs a **Rich Candidate Document** by combining their Headline, Summary, Top Skills, Education, and Career History.
    *   Applies **Recency Weighting** by prepending "CURRENT/RECENT ROLE:" to their most recent job description, giving it higher semantic prominence.
    *   Calculates Cosine Similarity against the encoded Job Description.

### Stage 3: Behavioral Signal Integration & Reasoning
*   **Goal:** Transform the semantic score into a final ranking by overlaying real-world hiring signals and generating explainable reasoning.
*   **Mechanism:**
    *   **Multipliers:** Applies compounding multipliers based on `redrob_signals` (e.g., +5% for high GitHub activity, +8% for Tier 1 education, penalty for short stints).
    *   **Deterministic Reasoning:** Generates a highly specific, human-readable reasoning string explaining exactly *why* the candidate was ranked there (e.g., noting their specific notice period, technical depth, or response rate).

---

## 🛠️ Tech Stack

*   **Backend:** Python 3.11, Flask
*   **AI/ML:** `sentence-transformers`, `scikit-learn`, `numpy`
*   **Frontend:** HTML5, CSS3 (Vanilla + Custom CSS Variables), Vanilla JavaScript
*   **Data Processing:** `json`, `re`, `tqdm`

---

## ⚙️ How to Run

### 1. Command Line Interface (CLI)

Run the ranking pipeline directly to generate a submission CSV:

```bash
python ranker.py --candidates candidates.jsonl --jd-config job_config.json --out submission.csv
```

### 2. Web Dashboard

Launch the interactive web UI:

```bash
python app.py
```
Then navigate to `http://localhost:5000` in your browser. From the dashboard, you can open the **⚙️ Configure** panel to modify the job description, upload new candidate data, and trigger the pipeline.

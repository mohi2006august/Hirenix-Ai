# 🚀 HirenixAI — Intelligent Candidate Discovery & Ranking Dashboard

HirenixAI is a premium, end-to-end recruitment solution designed to discover, filter, and intelligently rank candidates for highly specific roles. It combines a robust **three-stage candidate ranking pipeline** with a state-of-the-art **glassmorphic, dark-themed analytics dashboard** to deliver deep job understanding, semantic matching, and signal integration.

---

## 🌟 Key Features

### 🔍 1. Three-Stage AI Ranking Pipeline
- **Stage 1 (Fast Heuristic Filtering):** Screens candidates using rule-based criteria (e.g. ideal experience ranges of 5-9 years, tech keyword overlaps, current title mapping) and automatically weeds out non-technical roles or impossible/trap candidate records (honeypots).
- **Stage 2 (Dense Semantic Encoding):** Embeds profile headlines, summaries, and career history using `all-MiniLM-L6-v2` (a fast, CPU-friendly SentenceTransformer model) and ranks candidates by cosine similarity against the job description.
- **Stage 3 (Behavioral Signal Weighting):** Integrates behavioral metrics (e.g., recruiter response rates, notice periods, active statuses, interview completion rates) to compute the final suitability score.

### 📊 2. Premium Analytics Dashboard
- **Interactive Pipeline Funnel:** Visually traces candidate numbers as they are refined through each stage ($100,000 \rightarrow 2,000 \rightarrow 150 \rightarrow 100$).
- **Role Distribution Chart:** Displays candidate alignment across role categories (AI/ML, Research, Data Science, Search/Ranking, NLP).
- **Expert Skill Cloud:** Showcases the most common expert-level skills among top candidates.
- **Dynamic Leaderboard:** Interactive list of ranked candidates with search, filtering, and real-time score updates.

### 💡 3. Deep Candidate Context & Reasonings
- **"Why Selected" Engine:** Auto-generates detailed reasoning cards highlighting score breakdowns, custom strengths, potential concerns, and expert skills.
- **Role-Based Competitors Analysis:** Dynamic role category grouping that lists side-by-side matches competing for similar titles, complete with direct navigation links.

---

## 🏗️ Project Architecture

```
.
├── .gitignore
├── README.md                              # This file
└── India_runs_data_and_ai_challenge/      # Core project folder
    ├── app.py                             # Flask Web Server / API Backend
    ├── ranker.py                          # Pipeline Orchestration Script
    ├── requirements.txt                   # Python Dependencies
    ├── candidate_schema.json              # Structural reference for candidate metadata
    ├── pipeline/
    │   ├── stage1_filter.py               # Fast heuristic checks & honeypot removal
    │   ├── stage2_semantic.py             # SentenceTransformer semantic similarity
    │   └── stage3_signals.py              # Behavioral weights & deterministic explanation
    └── static/                            # Dashboard Frontend
        ├── index.html                     # HTML structure and layouts
        ├── style.css                      # Premium glassmorphic styling and transitions
        └── app.js                         # Dynamic rendering and modal handling
```

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, PyTorch, SentenceTransformers (`all-MiniLM-L6-v2`), Pandas, NumPy
- **Frontend:** Vanilla HTML5, CSS3 (Custom Glassmorphism, animations), Modern JavaScript (ES6+), FontAwesome
- **Data:** JSON Lines (`.jsonl`) processing

---

## 🚀 Getting Started

### 📋 Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 📥 1. Installation
1. Clone this repository and navigate to the project directory:
   ```bash
   cd India_runs_data_and_ai_challenge
   ```
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### ⚙️ 2. Run the Candidate Ranking Pipeline
To run the three-stage pipeline and generate the final `submission.csv` leaderboard:
```bash
python ranker.py --candidates path/to/candidates.jsonl --out submission.csv
```
> **Note:** The `candidates.jsonl` dataset file is excluded from Git tracking due to file size limits. Place your dataset file locally before running.

### 🖥️ 3. Start the Analytics Dashboard
To launch the Flask web application locally:
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your web browser to interact with the dashboard.

---

## ⚙️ How the Pipeline Works

### **Stage 1: Fast Heuristic Filter**
- Processes candidates in chunks for speed and low memory usage.
- Uses regex flags to eliminate non-matching occupations (e.g. marketing, accountants).
- Awards points for ideal experience ranges (5–9 years) and title keywords.

### **Stage 2: Dense Semantic Matching**
- Considers candidate summaries, headlines, and most recent career histories.
- Encodes candidate details alongside the extracted JD targets.
- Performs cosine similarity comparisons using `all-MiniLM-L6-v2` embeddings.

### **Stage 3: Behavioral Signal Integration**
- Applies scaling factors to semantic scores based on engagement criteria.
- **Positive boosts:** Notice periods $\le$ 30 days (+5%), high recruiter response rate (+10%), active open-to-work flag (+5%).
- **Negative penalties:** Extended notice period (-10%), low response rate (-20%), low interview completion rates (-30%).
- Automatically writes a concise, tailored reasoning string for each candidate.

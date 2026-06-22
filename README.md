# 🚀 HirenixAI — Architecture, Operations, and Scalability

HirenixAI is an intelligent, high-performance candidate discovery and ranking system. It features a multi-stage AI pipeline to process, filter, and score candidates, and a responsive web dashboard designed for enterprise recruiter access.

---

## 🏗️ 1. System Architecture

HirenixAI uses a funnel-based **multi-stage ranking architecture** to balance processing speed and computational depth:

```
[ Raw Candidate Pool (100,000+) ]
               │
               ▼
┌──────────────────────────────┐
│  Stage 1: Heuristic Filter   │  <-- Fast Regex & Heuristic Checks
└──────────────┬───────────────┘      O(1) memory, rules-based
               │  (Reduces to ~2,000)
               ▼
┌──────────────────────────────┐
│  Stage 2: Semantic Matching  │  <-- Dense Embeddings (all-MiniLM-L6-v2)
└──────────────┬───────────────┘      Cosine Similarity on CPU/GPU
               │  (Reduces to ~150)
               ▼
┌──────────────────────────────┐
│  Stage 3: Signal Adjustment   │  <-- Behavioral Weighting Multipliers
└──────────────┬───────────────┘      Deterministic Reasoning Engine
               │  (Reduces to exactly 100)
               ▼
┌──────────────────────────────┐
│     Final Ranked List        │  <-- Web Dashboard UI / Flask API
└──────────────────────────────┘
```

---

## ⚙️ 2. How It Works

### **Stage 1: Fast Heuristic Filter (stage1_filter.py)**
- **Streaming Chunks:** Streams candidate entries from a JSON Lines (`.jsonl`) file one line at a time to prevent high memory usage.
- **Trap/Honeypot Rejection:** Instantly discards non-technical titles (e.g. marketing, accountant) and candidates with extreme outliers in years of experience (e.g. >30 years) to prevent honeypot profiles from cluttering the pipeline.
- **Base Scoring:** Awards points for ideal experience ranges (5–9 years), relevant titles (AI/ML, Data Science, Search/Ranking), and high recruiter response rates.

### **Stage 2: Dense Semantic Matching (stage2_semantic.py)**
- **Document Construction:** Dynamically builds a textual representation of each candidate's profile, including headline, summary, skills list, and recent career history.
- **Sentence Embedding:** Embeds the job description text and candidate document text into a 384-dimensional dense vector space using `all-MiniLM-L6-v2`.
- **Similarity Scoring:** Calculates the cosine similarity between the job description vector and each candidate vector to determine their semantic fit.

### **Stage 3: Behavioral Signal Integration (stage3_signals.py)**
- **Signal Multipliers:** Modifies the semantic score by applying weight multipliers based on behavioral attributes:
  - **Favorable Notice Period ($\le 30$ days):** `+5%` score bonus.
  - **High Response Rate ($>80\%$):** `+10%` score bonus.
  - **Open-To-Work Flag:** `+5%` score bonus.
  - **Long Notice Period ($>60$ days):** `-10%` penalty.
  - **Low Response Rate ($<20\%$):** `-20%` penalty.
  - **Low Interview Completion Rate ($<50\%$):** `-30%` penalty.
- **Reasoning Engine:** Automatically writes a concise, contextual explanation explaining why the candidate was selected or highlighted (strengths, notice period availability, and core skills).

---

## 📈 3. Scalability Analysis

The system is designed to scale along two separate vectors: candidate data volume and concurrent recruiter/user traffic.

### **Candidate Pool Scalability (Data Layer)**
- **Current Capability (Up to 100,000+ Candidates):** 
  The python-based pipeline operates within a **5-minute time limit** and fits in **under 16 GB of CPU RAM**. Stage 1 runs in seconds on 100K profiles because it reads and filters candidate records as a stream.
- **Enterprise Scaling (Up to 10,000,000+ Candidates):**
  To scale to millions of candidates, we bypass real-time embedding generation of candidate profiles:
  1. **Pre-computed Embeddings:** Compute candidate profile vectors asynchronously when a candidate profile is updated or created.
  2. **Vector Databases:** Index candidate embedding vectors in a vector database (e.g., Qdrant, Milvus, or Pinecone) using HNSW (Hierarchical Navigable Small World) indices.
  3. **Sub-second Retrieval:** Querying the database with the embedded job description returns the top-K nearest neighbors in **milliseconds**, making Stage 2 scale at $O(\log N)$ instead of $O(N)$.

### **User Traffic Scalability (Concurrent Recruiters)**
- **Current Capability (Local Recruiter Workstation):** 
  The built-in Flask development server is single-threaded and handles a single recruiter looking up and scanning dashboards locally.
- **Enterprise Scaling (Up to 10,000+ Concurrent Recruiters):**
  To handle thousands of concurrent active recruiters accessing candidate profiles and ranking dashboards:
  1. **Production WSGI Server:** Deploy the Flask API backend using Gunicorn or UWSGI behind an Nginx reverse proxy.
  2. **Result Caching (Redis):** Cache candidate profile dashboards and ranks in-memory. Since job descriptions and candidate rankings do not change second-to-second, Redis can serve API requests in $<5\text{ms}$ with $O(1)$ read performance.
  3. **Load Balancing & Horizontal Scaling:** Run multiple stateless containerized instances of the Flask backend inside a Kubernetes cluster, scaling instances dynamically in response to request volume.

---

## 🌐 4. Website Features

The HirenixAI web dashboard is a fully interactive, glassmorphic dark-themed recruiter interface built with **vanilla HTML5, CSS3, and JavaScript (ES6+)**. Below is everything available on the website:

### **Pipeline Funnel Banner**
- Animated counter display showing how candidates flow through each stage: `100,000+ → 2,000 → 150 → 100`.
- Smooth ease-out cubic counting animation on page load, giving recruiters an instant overview of the filtering funnel.

### **Analytics Dashboard**
Three real-time analytics cards rendered from the `/api/stats` endpoint:
- **Score Distribution Chart** — Horizontal bar chart showing how many candidates fall into each semantic-fit score bucket (`0.90+`, `0.85–0.90`, `0.80–0.85`, etc.).
- **Top Skills Cloud** — A tag cloud of the most common advanced/expert-level skills across all 100 ranked candidates, with frequency counts.
- **Role Category Breakdown** — A ranked list showing candidate distribution across role categories (AI/ML Engineer, Data Scientist, NLP Engineer, Search/Ranking, AI Research, etc.).

### **Search, Filter & Sort Toolbar**
- **🔍 Live Search** — Real-time debounced search (200ms) across candidate name, title, company, location, skills, and candidate ID.
- **Role Category Filters** — One-click filter buttons: `All`, `AI/ML`, `Research`, `Data Sci`, `Search`, `NLP`.
- **Multi-Sort Options** — Sort candidates by Rank, Semantic Fit Score, Experience (high/low), Notice Period (shortest first), or Name (A–Z).

### **Candidate Ranking List**
- Staggered fade-in card animations for each candidate row.
- **Rank Badges** — Color-coded rank indicators: 🥇 Gold (Top 3), 🥈 Silver (Top 10), 🥉 Bronze (Top 25), Default (26–100).
- **Score Bars** — Visual progress bars with color gradients based on semantic fit (green for high, amber for mid, red for low).
- **Skill Pills** — Inline display of each candidate's top 3 advanced/expert skills.
- **Results Counter** — Dynamic display showing `Showing X of 100 candidates` based on active filters.

### **Candidate Detail Modal**
Clicking any candidate opens a rich detail modal with **5 tabbed views**:

1. **Why Selected** — AI-generated reasoning with:
   - Score breakdown (Semantic Fit, Experience Fit, JD Skill Matches, Availability).
   - Color-coded indicators (green/amber/red) for each metric.
   - Strengths list (e.g., "Strong semantic alignment", "Ideal experience level", "Active open-source contributor").
   - Potential concerns list (e.g., "Extended notice period", "Low recruiter response rate").
   - Key expert skills with proficiency duration in months.
   - Full AI-generated reasoning paragraph explaining the selection.

2. **Full Profile** — Complete candidate profile showing:
   - Professional summary.
   - All skills grouped and sorted by proficiency level (Expert → Advanced → Intermediate → Beginner).
   - Education history with institution name, degree, field of study, tier, and grade.

3. **Career History** — Interactive timeline view showing:
   - Job title, company, industry, and duration.
   - Current role highlighted with a green "Current" badge.
   - Job descriptions and date ranges.

4. **Behavioral Signals** — Visual gauge dashboard with 8 metrics:
   - Recruiter Response Rate, Interview Completion Rate, GitHub Activity Score, Profile Completeness Score, Notice Period, Offer Acceptance Rate, Profile Views (30d), Saved by Recruiters (30d).
   - Additional info cards: Open to Work status, Preferred Work Mode, Willingness to Relocate, Expected Salary Range (INR LPA).
   - Skill Assessment Scores rendered as horizontal bar charts.

5. **Competitors** — Side-by-side comparison view:
   - Lists all other candidates ranked in the same role category.
   - Shows each competitor's rank, score, title, experience, and top skills.
   - Click any competitor to navigate directly to their detail modal.

### **Candidate Comparison Matrix**
- **Checkbox Selection** — Select multiple candidates from the ranking list using checkboxes.
- **Floating Compare Drawer** — A sticky bottom drawer appears showing the count of selected candidates with `Clear` and `Compare Side-by-Side` buttons.
- **Comparison Table** — Opens a structured table comparing selected candidates across: Semantic Match Score, Experience, Availability, Top Skills, Strengths, and Concerns.

### **Theme Customizer**
- **5 Accent Color Themes** — Switch between Indigo, Emerald, Cyan, Rose, and Amber accent palettes with a single click.
- Theme changes apply globally across all UI components in real-time.

### **Design & UX**
- **Glassmorphic Dark Theme** — Premium dark UI with frosted-glass effects, subtle borders, and layered transparency.
- **Micro-Animations** — Smooth transitions on hover, modal open/close, counter animations, and staggered card entrances.
- **Responsive Layout** — Flexbox and CSS Grid-based layout that adapts to different screen sizes.
- **Keyboard Accessible** — `Escape` key to close modals, click-outside-to-dismiss behavior.

---

## 🛠️ 5. Tech Stack

- **AI/ML Layer:** PyTorch, SentenceTransformers (`all-MiniLM-L6-v2`), Scikit-learn (Cosine Similarity)
- **Data Engineering:** Python, Pandas, NumPy, JSON Lines
- **API & Backend:** Flask (REST APIs, Static File Serving)
- **Web Frontend:** Vanilla HTML5, Vanilla CSS3 (Glassmorphic dark design, micro-animations, flexbox/grid layout), JavaScript (ES6+, DOM rendering, asynchronous fetch APIs)

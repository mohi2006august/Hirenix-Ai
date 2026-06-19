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

## 🛠️ 4. Tech Stack

- **AI/ML Layer:** PyTorch, SentenceTransformers (`all-MiniLM-L6-v2`), Scikit-learn (Cosine Similarity)
- **Data Engineering:** Python, Pandas, NumPy, JSON Lines
- **API & Backend:** Flask (REST APIs, Static File Serving)
- **Web Frontend:** Vanilla HTML5, Vanilla CSS3 (Glassmorphic dark design, micro-animations, flexbox/grid layout), JavaScript (ES6+, DOM rendering, asynchronous fetch APIs)

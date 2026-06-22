"""
HirenixAI — Intelligent Candidate Discovery & Ranking Dashboard
Flask API backend that serves candidate data, analytics, and competitive analysis.
Now fully configurable — works with any job description and candidate dataset.
"""
import csv
import json
import os
import sys
import threading
import time
from collections import Counter, defaultdict
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# --- Setup Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# We will serve from frontend/dist if it exists, otherwise static (for backward compatibility)
FRONTEND_DIST = os.path.join(BASE_DIR, 'frontend', 'dist')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
CONFIG_PATH = os.path.join(BASE_DIR, 'job_config.json')
CANDIDATES_PATH = os.path.join(BASE_DIR, 'candidates.jsonl')
SUBMISSION_PATH = os.path.join(BASE_DIR, 'submission.csv')

# Add current dir to path for pipeline imports
sys.path.append(BASE_DIR)

app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

# ── Global data stores (loaded once at startup, reloaded on pipeline re-run) ──
RANKED_CANDIDATES = []      # Full candidate dicts, merged with ranking data
CANDIDATE_INDEX = {}        # candidate_id → full dict
ROLE_GROUPS = defaultdict(list)  # role_category → [candidate_ids]
JD_CONFIG = {}              # Active job config
PIPELINE_STATUS = {"running": False, "message": "Idle", "progress": 0}


# ── Config Loading ─────────────────────────────────────────────────────────────

def load_jd_config():
    """Load job config from job_config.json, with fallback defaults."""
    global JD_CONFIG
    
    defaults = {
        "job_title": "Senior AI/ML Engineer",
        "job_description": (
            "Senior AI Engineer with 5-9 years of experience. "
            "Deep technical depth in modern ML systems: embeddings, retrieval, ranking, LLMs, fine-tuning. "
            "Production experience with embeddings-based retrieval systems like sentence-transformers, BGE, E5. "
            "Experience with vector databases such as Pinecone, Weaviate, Qdrant, Milvus, FAISS. "
            "Hands-on experience with evaluation frameworks for ranking systems: NDCG, MRR, MAP, A/B testing. "
            "Strong Python programming skills. Ability to build end-to-end ranking and recommendation systems."
        ),
        "experience_range": [5, 9],
        "required_skills": [
            "embeddings", "retrieval", "ranking", "LLMs", "fine-tuning",
            "sentence-transformers", "BGE", "E5", "vector databases",
            "Pinecone", "Weaviate", "Qdrant", "Milvus", "FAISS",
            "NDCG", "MRR", "MAP", "A/B testing", "Python",
            "recommendation systems", "NLP", "deep learning",
            "PyTorch", "TensorFlow", "scikit-learn"
        ],
        "preferred_titles": [
            "ai engineer", "ml engineer", "machine learning engineer",
            "data scientist", "search engineer", "ranking engineer",
            "retrieval engineer", "nlp engineer", "recommendation engineer",
            "applied ml engineer", "senior ai engineer", "senior data scientist",
            "backend engineer", "data engineer"
        ],
        "reject_titles": [
            "marketing", "accountant", "customer support",
            "hardware", "mechanical"
        ],
        "pipeline_settings": {
            "stage1_top_k": 2000,
            "stage2_top_k": 150,
            "final_top_k": 100
        }
    }
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                JD_CONFIG = json.load(f)
            print(f"Loaded job config: {JD_CONFIG.get('job_title', 'N/A')}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load {CONFIG_PATH}: {e}. Using defaults.")
            JD_CONFIG = defaults
    else:
        print("No job_config.json found. Using defaults.")
        JD_CONFIG = defaults

def save_jd_config():
    """Save the current JD_CONFIG to disk."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(JD_CONFIG, f, indent=2, ensure_ascii=False)


# ── Role Auto-Detection ──────────────────────────────────────────────────────

def auto_detect_role_category(title: str) -> str:
    """
    Automatically categorize a candidate's title into a role category.
    Uses the preferred_titles from config + common pattern matching.
    """
    title_lower = title.lower().strip()
    
    # Common role category patterns (ordered by specificity)
    ROLE_PATTERNS = [
        # AI/ML
        (["ai engineer", "ml engineer", "machine learning engineer", "applied ml", "senior ai engineer"], "AI/ML Engineer"),
        (["ai research", "ai specialist", "research scientist", "research engineer"], "AI Research"),
        # Data Science
        (["data scientist", "senior data scientist", "lead data scientist"], "Data Scientist"),
        # NLP
        (["nlp engineer", "natural language", "computational linguist"], "NLP Engineer"),
        # Search/Ranking/Retrieval
        (["search engineer", "ranking engineer", "retrieval engineer", "recommendation"], "Search/Ranking"),
        # Backend/Software (ML)
        (["software engineer", "backend engineer", "senior software engineer"], "Software Engineer (ML)"),
        # Data Engineering
        (["data engineer", "analytics engineer", "etl engineer"], "Data Engineer"),
        # Junior/Entry
        (["junior", "intern", "trainee", "associate"], "Junior/Entry Level"),
        # Management
        (["manager", "director", "head of", "vp of", "lead"], "Leadership"),
        # Frontend/Full-stack
        (["frontend", "front-end", "full stack", "fullstack", "react", "angular", "vue"], "Frontend/Full-Stack"),
        # DevOps/Infra
        (["devops", "sre", "infrastructure", "platform engineer", "cloud engineer"], "DevOps/Infra"),
        # Product/Design
        (["product manager", "product owner", "ux designer", "ui designer"], "Product/Design"),
    ]
    
    for keywords, category in ROLE_PATTERNS:
        for kw in keywords:
            if kw in title_lower:
                return category
    
    return "Other"


def generate_why_selected(candidate: dict) -> dict:
    """
    Generate a detailed, structured 'why selected' reasoning for a candidate.
    Returns a dict with multiple reasoning dimensions.
    Uses JD_CONFIG for dynamic skill matching and experience range.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    score = candidate.get("score", 0)
    
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Unknown")
    
    # ── Skill matching (from config) ──
    candidate_skill_names = [s["name"].lower() for s in skills]
    jd_skills_lower = [s.lower() for s in JD_CONFIG.get("required_skills", [])]
    
    matched_skills = []
    for s in skills:
        if s["name"].lower() in jd_skills_lower:
            matched_skills.append(s)
    
    advanced_skills = [s for s in skills if s.get("proficiency") in ("advanced", "expert")]
    
    # ── Experience analysis (from config) ──
    exp_range = JD_CONFIG.get("experience_range", [5, 9])
    exp_min = exp_range[0] if len(exp_range) > 0 else 5
    exp_max = exp_range[1] if len(exp_range) > 1 else 9
    exp_fit = "perfect" if exp_min <= yoe <= exp_max else ("over-qualified" if yoe > exp_max else "developing")
    
    # ── Signal analysis ──
    np_days = signals.get("notice_period_days", 60)
    rr = signals.get("recruiter_response_rate", 0)
    icr = signals.get("interview_completion_rate", 1.0)
    otw = signals.get("open_to_work_flag", False)
    github = signals.get("github_activity_score", 0)
    profile_score = signals.get("profile_completeness_score", 0)
    
    availability = "Immediate" if np_days <= 15 else ("Short" if np_days <= 30 else ("Standard" if np_days <= 60 else "Extended"))
    
    # ── Career trajectory ──
    career_highlights = []
    for job in career[:3]:
        career_highlights.append({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "duration_months": job.get("duration_months", 0),
            "is_current": job.get("is_current", False)
        })
    
    # ── Build structured reasoning ──
    strengths = []
    concerns = []
    
    # Score-based
    if score >= 0.85:
        strengths.append("Exceptionally high semantic alignment with the job description")
    elif score >= 0.75:
        strengths.append("Strong semantic alignment with the job description")
    else:
        strengths.append("Moderate semantic alignment with the job description")
    
    # Experience
    if exp_fit == "perfect":
        strengths.append(f"Ideal experience level ({yoe:.1f} years) for the target range of {exp_min}-{exp_max} years")
    elif exp_fit == "over-qualified":
        strengths.append(f"Highly experienced ({yoe:.1f} years) — brings senior-level depth")
        if yoe > 15:
            concerns.append("Significantly over the target experience range — may expect a more senior role")
    
    # Skills
    if len(matched_skills) >= 3:
        strengths.append(f"Strong JD skill overlap: {', '.join(s['name'] for s in matched_skills[:5])}")
    if len(advanced_skills) >= 3:
        strengths.append(f"Deep expertise ({len(advanced_skills)} advanced/expert-level skills)")
    
    # Behavioral signals
    if otw:
        strengths.append("Actively open to new opportunities")
    if rr >= 0.7:
        strengths.append(f"Highly responsive to recruiters ({rr:.0%} response rate)")
    elif rr < 0.3:
        concerns.append(f"Low recruiter response rate ({rr:.0%}) — may be passive or selective")
    
    if icr >= 0.8:
        strengths.append("Excellent interview completion track record")
    elif icr < 0.5:
        concerns.append(f"Low interview completion rate ({icr:.0%}) — potential dropout risk")
    
    if github >= 7:
        strengths.append(f"Active open-source contributor (GitHub score: {github:.1f}/10)")
    
    if np_days <= 30:
        strengths.append(f"Quick availability ({np_days}-day notice period)")
    elif np_days > 60:
        concerns.append(f"Extended notice period ({np_days} days) may delay onboarding")
    
    # Title relevance
    role_cat = auto_detect_role_category(title)
    relevant_roles = {"AI/ML Engineer", "AI Research", "NLP Engineer", "Search/Ranking", "Data Scientist"}
    if role_cat in relevant_roles:
        strengths.append(f"Current role ({title}) is directly relevant to the position")
    
    return {
        "score_breakdown": {
            "semantic_fit": round(score, 4),
            "experience_fit": exp_fit,
            "years_of_experience": yoe,
            "matched_jd_skills": len(matched_skills),
            "total_advanced_skills": len(advanced_skills),
            "availability": availability,
            "notice_period_days": np_days
        },
        "strengths": strengths,
        "concerns": concerns if concerns else ["No significant concerns identified"],
        "career_highlights": career_highlights,
        "key_skills": [{"name": s["name"], "proficiency": s.get("proficiency", ""), "months": s.get("duration_months", 0)} for s in advanced_skills[:8]],
        "behavioral_signals": {
            "open_to_work": otw,
            "recruiter_response_rate": rr,
            "interview_completion_rate": icr,
            "github_activity": github,
            "profile_completeness": profile_score
        }
    }


def load_data():
    """Load submission.csv and merge with full candidate data from candidates.jsonl."""
    global RANKED_CANDIDATES, CANDIDATE_INDEX, ROLE_GROUPS
    
    # Reset
    RANKED_CANDIDATES = []
    CANDIDATE_INDEX = {}
    ROLE_GROUPS = defaultdict(list)
    
    # 1. Read submission.csv
    if not os.path.exists(SUBMISSION_PATH):
        print("Warning: submission.csv not found. Dashboard will be empty until pipeline is run.")
        return
    
    ranked = {}
    with open(SUBMISSION_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ranked[row["candidate_id"]] = {
                "rank": int(row["rank"]),
                "score": float(row["score"]),
                "reasoning": row["reasoning"]
            }
    
    ranked_ids = set(ranked.keys())
    
    # 2. Read candidates file and extract only ranked candidates
    candidates_file = CANDIDATES_PATH
    if not os.path.exists(candidates_file):
        print(f"Warning: {candidates_file} not found. Showing ranking data only.")
        # Still show what we have from submission.csv
        for cid, rank_info in ranked.items():
            candidate = {"candidate_id": cid, "profile": {}, "skills": [], "redrob_signals": {}, "career_history": []}
            candidate.update(rank_info)
            candidate["why_selected"] = generate_why_selected(candidate)
            candidate["role_category"] = "Other"
            ROLE_GROUPS["Other"].append(cid)
            RANKED_CANDIDATES.append(candidate)
            CANDIDATE_INDEX[cid] = candidate
        RANKED_CANDIDATES.sort(key=lambda x: x["rank"])
        return
    
    full_data = {}
    print(f"Loading {len(ranked_ids)} ranked candidates from {candidates_file}...")
    with open(candidates_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                c = json.loads(line)
                cid = c.get("candidate_id", "")
                if cid in ranked_ids:
                    full_data[cid] = c
                    if len(full_data) == len(ranked_ids):
                        break  # found all, stop early
            except json.JSONDecodeError:
                continue
    
    # 3. Merge and build final list
    for cid, rank_info in ranked.items():
        candidate = full_data.get(cid, {"candidate_id": cid, "profile": {}, "skills": [], "redrob_signals": {}, "career_history": []})
        candidate.update(rank_info)
        
        # Generate detailed reasoning
        candidate["why_selected"] = generate_why_selected(candidate)
        
        # Categorize role (auto-detect)
        title = candidate.get("profile", {}).get("current_title", "")
        role_cat = auto_detect_role_category(title)
        candidate["role_category"] = role_cat
        ROLE_GROUPS[role_cat].append(cid)
        
        RANKED_CANDIDATES.append(candidate)
        CANDIDATE_INDEX[cid] = candidate
    
    # Sort by rank
    RANKED_CANDIDATES.sort(key=lambda x: x["rank"])
    print(f"Loaded {len(RANKED_CANDIDATES)} candidates across {len(ROLE_GROUPS)} role categories.")


# ── Pipeline Execution ───────────────────────────────────────────────────────

def run_pipeline_thread():
    """Run the full pipeline in a background thread."""
    global PIPELINE_STATUS
    
    try:
        from pipeline.stage1_filter import process_file_in_chunks
        from pipeline.stage2_semantic import semantic_rank
        from pipeline.stage3_signals import apply_signals_and_reasoning
        
        PIPELINE_STATUS = {"running": True, "message": "Stage 1: Heuristic Filtering...", "progress": 10}
        
        pipeline_settings = JD_CONFIG.get("pipeline_settings", {})
        stage1_top_k = pipeline_settings.get("stage1_top_k", 2000)
        stage2_top_k = pipeline_settings.get("stage2_top_k", 150)
        final_top_k = pipeline_settings.get("final_top_k", 100)
        
        # Stage 1
        top_k_filtered = process_file_in_chunks(CANDIDATES_PATH, jd_config=JD_CONFIG, top_k=stage1_top_k)
        PIPELINE_STATUS = {"running": True, "message": f"Stage 1 complete. {len(top_k_filtered)} candidates. Running Stage 2...", "progress": 40}
        
        # Stage 2
        jd_text = JD_CONFIG.get("job_description", "")
        semantically_ranked = semantic_rank(top_k_filtered, jd_text=jd_text, top_k=stage2_top_k)
        PIPELINE_STATUS = {"running": True, "message": f"Stage 2 complete. {len(semantically_ranked)} candidates. Running Stage 3...", "progress": 75}
        
        # Stage 3
        final_ranked = apply_signals_and_reasoning(semantically_ranked, final_top_k=final_top_k)
        PIPELINE_STATUS = {"running": True, "message": "Writing results...", "progress": 90}
        
        # Write submission.csv
        with open(SUBMISSION_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for c in final_ranked:
                writer.writerow([
                    c['candidate_id'],
                    c['rank'],
                    f"{c['final_score']:.4f}",
                    c['reasoning']
                ])
        
        # Reload dashboard data
        load_data()
        
        PIPELINE_STATUS = {"running": False, "message": f"Complete! Ranked {len(final_ranked)} candidates.", "progress": 100}
        print(f"Pipeline complete. Ranked {len(final_ranked)} candidates.")
        
    except Exception as e:
        PIPELINE_STATUS = {"running": False, "message": f"Error: {str(e)}", "progress": 0}
        print(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/candidates")
def api_candidates():
    """Return all ranked candidates (summary view)."""
    result = []
    for c in RANKED_CANDIDATES:
        profile = c.get("profile", {})
        signals = c.get("redrob_signals", {})
        skills = c.get("skills", [])
        top_skills = [s["name"] for s in skills if s.get("proficiency") in ("advanced", "expert")][:5]
        
        result.append({
            "candidate_id": c["candidate_id"],
            "rank": c["rank"],
            "score": c["score"],
            "name": profile.get("anonymized_name", "Unknown"),
            "title": profile.get("current_title", ""),
            "company": profile.get("current_company", ""),
            "location": profile.get("location", ""),
            "years_of_experience": profile.get("years_of_experience", 0),
            "top_skills": top_skills,
            "role_category": c.get("role_category", "Other"),
            "open_to_work": signals.get("open_to_work_flag", False),
            "notice_period_days": signals.get("notice_period_days", 0),
            "reasoning": c.get("reasoning", "")
        })
    return jsonify(result)


@app.route("/api/candidates/<candidate_id>")
def api_candidate_detail(candidate_id):
    """Return full detail for a single candidate, including why_selected and competitors."""
    candidate = CANDIDATE_INDEX.get(candidate_id)
    if not candidate:
        return jsonify({"error": "Candidate not found"}), 404
    
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])
    
    # Build competitors list (same role category, excluding self)
    role_cat = candidate.get("role_category", "Other")
    competitor_ids = [cid for cid in ROLE_GROUPS.get(role_cat, []) if cid != candidate_id]
    competitors = []
    for cid in competitor_ids:
        comp = CANDIDATE_INDEX.get(cid, {})
        comp_profile = comp.get("profile", {})
        comp_skills = comp.get("skills", [])
        competitors.append({
            "candidate_id": cid,
            "rank": comp.get("rank", 0),
            "score": comp.get("score", 0),
            "name": comp_profile.get("anonymized_name", "Unknown"),
            "title": comp_profile.get("current_title", ""),
            "years_of_experience": comp_profile.get("years_of_experience", 0),
            "top_skills": [s["name"] for s in comp_skills if s.get("proficiency") in ("advanced", "expert")][:4]
        })
    competitors.sort(key=lambda x: x["rank"])
    
    return jsonify({
        "candidate_id": candidate["candidate_id"],
        "rank": candidate["rank"],
        "score": candidate["score"],
        "role_category": role_cat,
        "reasoning": candidate.get("reasoning", ""),
        "why_selected": candidate.get("why_selected", {}),
        "profile": {
            "name": profile.get("anonymized_name", ""),
            "headline": profile.get("headline", ""),
            "summary": profile.get("summary", ""),
            "location": profile.get("location", ""),
            "country": profile.get("country", ""),
            "years_of_experience": profile.get("years_of_experience", 0),
            "current_title": profile.get("current_title", ""),
            "current_company": profile.get("current_company", ""),
            "current_company_size": profile.get("current_company_size", ""),
            "current_industry": profile.get("current_industry", "")
        },
        "skills": [
            {"name": s["name"], "proficiency": s.get("proficiency", ""), "endorsements": s.get("endorsements", 0), "duration_months": s.get("duration_months", 0)}
            for s in skills
        ],
        "career_history": [
            {
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "start_date": j.get("start_date", ""),
                "end_date": j.get("end_date"),
                "duration_months": j.get("duration_months", 0),
                "is_current": j.get("is_current", False),
                "industry": j.get("industry", ""),
                "description": j.get("description", "")
            }
            for j in career
        ],
        "education": [
            {
                "institution": e.get("institution", ""),
                "degree": e.get("degree", ""),
                "field_of_study": e.get("field_of_study", ""),
                "tier": e.get("tier", ""),
                "grade": e.get("grade", "")
            }
            for e in education
        ],
        "signals": {
            "profile_completeness": signals.get("profile_completeness_score", 0),
            "open_to_work": signals.get("open_to_work_flag", False),
            "notice_period_days": signals.get("notice_period_days", 0),
            "recruiter_response_rate": signals.get("recruiter_response_rate", 0),
            "interview_completion_rate": signals.get("interview_completion_rate", 0),
            "github_activity": signals.get("github_activity_score", 0),
            "applications_30d": signals.get("applications_submitted_30d", 0),
            "profile_views_30d": signals.get("profile_views_received_30d", 0),
            "saved_by_recruiters_30d": signals.get("saved_by_recruiters_30d", 0),
            "offer_acceptance_rate": signals.get("offer_acceptance_rate", 0),
            "expected_salary": signals.get("expected_salary_range_inr_lpa", {}),
            "preferred_work_mode": signals.get("preferred_work_mode", ""),
            "willing_to_relocate": signals.get("willing_to_relocate", False),
            "skill_assessments": signals.get("skill_assessment_scores", {})
        },
        "competitors": competitors
    })


@app.route("/api/stats")
def api_stats():
    """Aggregate analytics for the dashboard header."""
    if not RANKED_CANDIDATES:
        return jsonify({
            "total_candidates_scanned": 0,
            "stage1_filtered": 0,
            "stage2_semantic": 0,
            "final_ranked": 0,
            "avg_score": 0,
            "max_score": 0,
            "min_score": 0,
            "avg_experience": 0,
            "score_distribution": {},
            "experience_distribution": {},
            "top_skills": [],
            "role_distribution": {},
            "job_title": JD_CONFIG.get("job_title", "N/A")
        })
    
    scores = [c["score"] for c in RANKED_CANDIDATES]
    experiences = [c.get("profile", {}).get("years_of_experience", 0) for c in RANKED_CANDIDATES]
    
    # Skill frequency
    skill_counter = Counter()
    for c in RANKED_CANDIDATES:
        for s in c.get("skills", []):
            if s.get("proficiency") in ("advanced", "expert"):
                skill_counter[s["name"]] += 1
    
    # Score distribution buckets
    score_buckets = {"0.90+": 0, "0.85-0.90": 0, "0.80-0.85": 0, "0.75-0.80": 0, "0.70-0.75": 0, "<0.70": 0}
    for s in scores:
        if s >= 0.90: score_buckets["0.90+"] += 1
        elif s >= 0.85: score_buckets["0.85-0.90"] += 1
        elif s >= 0.80: score_buckets["0.80-0.85"] += 1
        elif s >= 0.75: score_buckets["0.75-0.80"] += 1
        elif s >= 0.70: score_buckets["0.70-0.75"] += 1
        else: score_buckets["<0.70"] += 1
    
    # Experience distribution
    exp_buckets = {"0-2 yrs": 0, "2-4 yrs": 0, "4-6 yrs": 0, "6-8 yrs": 0, "8-10 yrs": 0, "10+ yrs": 0}
    for e in experiences:
        if e < 2: exp_buckets["0-2 yrs"] += 1
        elif e < 4: exp_buckets["2-4 yrs"] += 1
        elif e < 6: exp_buckets["4-6 yrs"] += 1
        elif e < 8: exp_buckets["6-8 yrs"] += 1
        elif e < 10: exp_buckets["8-10 yrs"] += 1
        else: exp_buckets["10+ yrs"] += 1
    
    # Role distribution (dynamic from actual data)
    role_dist = {cat: len(ids) for cat, ids in ROLE_GROUPS.items()}
    
    # Pipeline settings for dynamic counter display
    pipeline_settings = JD_CONFIG.get("pipeline_settings", {})
    
    return jsonify({
        "total_candidates_scanned": pipeline_settings.get("stage1_top_k", 2000) * 50,  # Estimate
        "stage1_filtered": pipeline_settings.get("stage1_top_k", 2000),
        "stage2_semantic": pipeline_settings.get("stage2_top_k", 150),
        "final_ranked": len(RANKED_CANDIDATES),
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "max_score": round(max(scores), 4) if scores else 0,
        "min_score": round(min(scores), 4) if scores else 0,
        "avg_experience": round(sum(experiences) / len(experiences), 1) if experiences else 0,
        "score_distribution": score_buckets,
        "experience_distribution": exp_buckets,
        "top_skills": skill_counter.most_common(20),
        "role_distribution": role_dist,
        "job_title": JD_CONFIG.get("job_title", "N/A")
    })


# ── Config API ────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def api_get_config():
    """Return the current active job config."""
    return jsonify(JD_CONFIG)


@app.route("/api/config", methods=["POST"])
def api_update_config():
    """Update the job config. Expects JSON body with config fields."""
    global JD_CONFIG
    
    try:
        new_config = request.get_json()
        if not new_config:
            return jsonify({"error": "No JSON body provided"}), 400
        
        # Merge with existing config (allows partial updates)
        JD_CONFIG.update(new_config)
        
        # Save to disk
        save_jd_config()
        
        return jsonify({"status": "ok", "message": "Config updated successfully", "config": JD_CONFIG})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Candidate Upload API ──────────────────────────────────────────────────────

@app.route("/api/upload-candidates", methods=["POST"])
def api_upload_candidates():
    """Upload a new candidates JSONL file."""
    global CANDIDATES_PATH
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided. Use multipart/form-data with field name 'file'."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    # Save the uploaded file
    upload_path = os.path.join(BASE_DIR, 'candidates.jsonl')
    file.save(upload_path)
    CANDIDATES_PATH = upload_path
    
    # Count lines to give user feedback
    line_count = 0
    with open(upload_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                line_count += 1
    
    return jsonify({
        "status": "ok",
        "message": f"Uploaded {file.filename} with {line_count:,} candidates.",
        "candidates_count": line_count,
        "path": upload_path
    })


@app.route("/api/set-candidates-path", methods=["POST"])
def api_set_candidates_path():
    """Set the path to a candidates JSONL file already on disk."""
    global CANDIDATES_PATH
    
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "Provide 'path' in JSON body"}), 400
    
    path = data['path']
    if not os.path.exists(path):
        return jsonify({"error": f"File not found: {path}"}), 404
    
    CANDIDATES_PATH = path
    
    # Count lines
    line_count = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                line_count += 1
    
    return jsonify({
        "status": "ok",
        "message": f"Set candidates path to {path} ({line_count:,} candidates).",
        "candidates_count": line_count
    })


# ── Pipeline Execution API ────────────────────────────────────────────────────

@app.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    """Trigger a full pipeline re-run with current config and data."""
    global PIPELINE_STATUS
    
    if PIPELINE_STATUS["running"]:
        return jsonify({"error": "Pipeline is already running.", "status": PIPELINE_STATUS}), 409
    
    if not os.path.exists(CANDIDATES_PATH):
        return jsonify({"error": f"Candidates file not found: {CANDIDATES_PATH}"}), 404
    
    # Start pipeline in background thread
    thread = threading.Thread(target=run_pipeline_thread, daemon=True)
    thread.start()
    
    return jsonify({"status": "ok", "message": "Pipeline started.", "pipeline_status": PIPELINE_STATUS})


@app.route("/api/pipeline-status")
def api_pipeline_status():
    """Check the current pipeline execution status."""
    return jsonify(PIPELINE_STATUS)


# ── Bootstrap ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_jd_config()
    load_data()
    print(f"\n>>> HirenixAI Dashboard running at http://localhost:5000")
    print(f">>> Job Config: {JD_CONFIG.get('job_title', 'N/A')}")
    print(f">>> Candidates: {CANDIDATES_PATH}\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

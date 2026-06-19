"""
HirenixAI — Intelligent Candidate Discovery & Ranking Dashboard
Flask API backend that serves candidate data, analytics, and competitive analysis.
"""
import csv
import json
import os
from collections import Counter, defaultdict
from flask import Flask, jsonify, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR)

# ── Global data stores (loaded once at startup) ──────────────────────────────
RANKED_CANDIDATES = []      # Full candidate dicts, merged with ranking data
CANDIDATE_INDEX = {}        # candidate_id → full dict
ROLE_GROUPS = defaultdict(list)  # role_category → [candidate_ids]

# ── JD context for "why selected" reasoning ───────────────────────────────────
JD_REQUIREMENTS = {
    "title": "Senior AI/ML Engineer",
    "experience_range": (5, 9),
    "core_skills": [
        "embeddings", "retrieval", "ranking", "LLMs", "fine-tuning",
        "sentence-transformers", "BGE", "E5", "vector databases",
        "Pinecone", "Weaviate", "Qdrant", "Milvus", "FAISS",
        "NDCG", "MRR", "MAP", "A/B testing", "Python",
        "recommendation systems", "NLP", "deep learning",
        "PyTorch", "TensorFlow", "scikit-learn"
    ],
    "role_keywords": [
        "AI", "ML", "Machine Learning", "Data Scientist",
        "Search", "NLP", "Ranking", "Retrieval", "Recommendation"
    ]
}

# ── Role categorization ──────────────────────────────────────────────────────
ROLE_CATEGORIES = {
    "AI/ML Engineer": ["ai engineer", "ml engineer", "machine learning engineer", "applied ml engineer", "senior ai engineer"],
    "AI Research": ["ai research engineer", "ai specialist"],
    "Data Scientist": ["data scientist", "senior data scientist"],
    "NLP Engineer": ["nlp engineer", "senior nlp engineer"],
    "Search/Ranking": ["search engineer", "recommendation systems engineer"],
    "Software Engineer (ML)": ["senior software engineer (ml)", "senior software engineer"],
    "Junior ML": ["junior ml engineer"],
}

def categorize_role(title: str) -> str:
    """Map a candidate title to a broader role category."""
    title_lower = title.lower().strip()
    for category, keywords in ROLE_CATEGORIES.items():
        for kw in keywords:
            if kw in title_lower:
                return category
    return "Other"


def generate_why_selected(candidate: dict) -> dict:
    """
    Generate a detailed, structured 'why selected' reasoning for a candidate.
    Returns a dict with multiple reasoning dimensions.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    score = candidate.get("score", 0)
    
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Unknown")
    
    # ── Skill matching ──
    candidate_skill_names = [s["name"].lower() for s in skills]
    jd_skills_lower = [s.lower() for s in JD_REQUIREMENTS["core_skills"]]
    
    matched_skills = []
    for s in skills:
        if s["name"].lower() in jd_skills_lower:
            matched_skills.append(s)
    
    advanced_skills = [s for s in skills if s.get("proficiency") in ("advanced", "expert")]
    
    # ── Experience analysis ──
    exp_min, exp_max = JD_REQUIREMENTS["experience_range"]
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
    role_cat = categorize_role(title)
    if role_cat in ("AI/ML Engineer", "AI Research", "NLP Engineer", "Search/Ranking"):
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
    
    # 1. Read submission.csv
    submission_path = os.path.join(BASE_DIR, "submission.csv")
    ranked = {}
    with open(submission_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ranked[row["candidate_id"]] = {
                "rank": int(row["rank"]),
                "score": float(row["score"]),
                "reasoning": row["reasoning"]
            }
    
    ranked_ids = set(ranked.keys())
    
    # 2. Read candidates.jsonl and extract only ranked candidates
    candidates_path = os.path.join(BASE_DIR, "candidates.jsonl")
    full_data = {}
    
    print(f"Loading {len(ranked_ids)} ranked candidates from candidates.jsonl...")
    with open(candidates_path, "r", encoding="utf-8") as f:
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
        
        # Categorize role
        title = candidate.get("profile", {}).get("current_title", "")
        role_cat = categorize_role(title)
        candidate["role_category"] = role_cat
        ROLE_GROUPS[role_cat].append(cid)
        
        RANKED_CANDIDATES.append(candidate)
        CANDIDATE_INDEX[cid] = candidate
    
    # Sort by rank
    RANKED_CANDIDATES.sort(key=lambda x: x["rank"])
    print(f"Loaded {len(RANKED_CANDIDATES)} candidates across {len(ROLE_GROUPS)} role categories.")


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/candidates")
def api_candidates():
    """Return all 100 ranked candidates (summary view)."""
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
    exp_buckets = {"3-4 yrs": 0, "4-5 yrs": 0, "5-6 yrs": 0, "6-7 yrs": 0, "7-8 yrs": 0, "8+ yrs": 0}
    for e in experiences:
        if e < 4: exp_buckets["3-4 yrs"] += 1
        elif e < 5: exp_buckets["4-5 yrs"] += 1
        elif e < 6: exp_buckets["5-6 yrs"] += 1
        elif e < 7: exp_buckets["6-7 yrs"] += 1
        elif e < 8: exp_buckets["7-8 yrs"] += 1
        else: exp_buckets["8+ yrs"] += 1
    
    # Role distribution
    role_dist = {cat: len(ids) for cat, ids in ROLE_GROUPS.items()}
    
    return jsonify({
        "total_candidates_scanned": 100000,
        "stage1_filtered": 2000,
        "stage2_semantic": 150,
        "final_ranked": len(RANKED_CANDIDATES),
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "max_score": round(max(scores), 4) if scores else 0,
        "min_score": round(min(scores), 4) if scores else 0,
        "avg_experience": round(sum(experiences) / len(experiences), 1) if experiences else 0,
        "score_distribution": score_buckets,
        "experience_distribution": exp_buckets,
        "top_skills": skill_counter.most_common(20),
        "role_distribution": role_dist
    })


# ── Bootstrap ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_data()
    print("\n>>> HirenixAI Dashboard running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

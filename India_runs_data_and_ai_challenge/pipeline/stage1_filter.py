import json
import re
from typing import List, Dict, Any, Optional
from tqdm import tqdm

def process_file_in_chunks(file_path: str, jd_config: Optional[Dict] = None, top_k: int = 2000) -> List[Dict[Any, Any]]:
    """
    Reads candidates.jsonl line by line.
    Calculates a fast heuristic score based on JD config keywords, experience, and title.
    Includes Honeypot Detection: Rejects candidates with tech skills but no technical career history.
    """
    if jd_config is None:
        jd_config = {}
    
    pipeline_settings = jd_config.get('pipeline_settings', {})
    top_k = pipeline_settings.get('stage1_top_k', top_k)
    
    preferred_titles = jd_config.get('preferred_titles', [])
    reject_titles = jd_config.get('reject_titles', [])
    required_skills = jd_config.get('required_skills', [])
    tech_keywords = set(kw.lower() for kw in required_skills)
    
    ai_title_pattern = re.compile(r'(' + '|'.join(re.escape(t) for t in preferred_titles) + ')', re.IGNORECASE) if preferred_titles else None
    trap_title_pattern = re.compile(r'(' + '|'.join(re.escape(t) for t in reject_titles) + ')', re.IGNORECASE) if reject_titles else None
    
    # Generic tech keywords to look for in career descriptions to validate they actually did tech work
    tech_career_pattern = re.compile(r'(data|model|algorithm|code|software|engineer|develop|train|deploy|machine learning|ai|python|sql|cloud|infrastructure|architecture|system|api|backend|frontend)', re.IGNORECASE)

    exp_range = jd_config.get('experience_range', [5, 9])
    exp_min = exp_range[0] if len(exp_range) > 0 else 5
    exp_max = exp_range[1] if len(exp_range) > 1 else 9
    exp_extended_min = max(0, exp_min - 1)
    exp_extended_max = exp_max + 3

    candidates_scored = []
    
    # Try loading as a full JSON array first, fallback to JSONL
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                candidates_to_process = data
            else:
                candidates_to_process = [data]
    except json.JSONDecodeError:
        # Fallback to JSONL
        candidates_to_process = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        candidates_to_process.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    for c in tqdm(candidates_to_process, desc="Stage 1: Fast Heuristic Filtering"):
        profile = c.get('profile', {})
        yoe = profile.get('years_of_experience', 0)
        title = profile.get('current_title', '')
            
        # 1. Base Outlier Rejection
        if yoe > 30: # Likely data artifact
            continue
        
        # 2. Trap Title Rejection
        if trap_title_pattern and trap_title_pattern.search(title):
            continue
            
        # 3. Honeypot Check: Career History Relevance
        career_history = c.get('career_history', [])
        has_tech_experience = False
        career_text_combined = ""
        for job in career_history:
            desc = job.get('description', '')
            job_title = job.get('title', '')
            career_text_combined += f"{job_title} {desc} "
            if tech_career_pattern.search(desc) or tech_career_pattern.search(job_title):
                has_tech_experience = True
                
        # If they have no tech keywords in their entire career history, but we are looking for a tech role, they are a honeypot.
        # Only apply this strict filter if we are actually looking for tech skills (which we are, based on required_skills)
        if required_skills and not has_tech_experience and len(career_history) > 0:
             continue # Honeypot caught
        
        score = 0.0
        
        # Experience scoring
        if exp_min <= yoe <= exp_max:
            score += 5.0
        elif exp_extended_min <= yoe <= exp_extended_max:
            score += 2.0
            
        # Title scoring
        if ai_title_pattern and ai_title_pattern.search(title):
            score += 5.0 # Increased weight for good titles
            
        # Headline/Summary coherence
        headline = profile.get('headline', '')
        summary = profile.get('summary', '')
        combined_intro = f"{headline} {summary}".lower()
        
        intro_tech_matches = 0
        for kw in tech_keywords:
            if kw in combined_intro:
                intro_tech_matches += 1
        if intro_tech_matches > 0:
            score += min(intro_tech_matches, 3) * 1.0 # Cap summary bonus
        
        # Skill Trust Scoring
        skills = c.get('skills', [])
        for s in skills:
            name = s.get('name', '').lower()
            if name in tech_keywords:
                # Base point for having the skill
                skill_score = 1.0
                
                # Multipliers based on trust factors
                prof = s.get('proficiency', 'beginner')
                if prof == 'expert': skill_score *= 2.0
                elif prof == 'advanced': skill_score *= 1.5
                elif prof == 'intermediate': skill_score *= 1.2
                
                endorsements = s.get('endorsements', 0)
                if endorsements > 20: skill_score *= 1.5
                elif endorsements > 5: skill_score *= 1.2
                
                duration = s.get('duration_months', 0)
                if duration > 24: skill_score *= 1.3
                elif duration > 12: skill_score *= 1.1
                
                score += skill_score
                
        # Basic Behavioral sanity
        signals = c.get('redrob_signals', {})
        if signals.get('open_to_work_flag'):
            score += 1.0
        if signals.get('recruiter_response_rate', 0) > 0.5:
            score += 1.0
            
        c['_heuristic_score'] = score
        candidates_scored.append(c)

    candidates_scored.sort(key=lambda x: x['_heuristic_score'], reverse=True)
    return candidates_scored[:top_k]

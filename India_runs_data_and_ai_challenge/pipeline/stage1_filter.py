import json
import re
from typing import List, Dict, Any, Optional
from tqdm import tqdm

def process_file_in_chunks(file_path: str, jd_config: Optional[Dict] = None, top_k: int = 2000) -> List[Dict[Any, Any]]:
    """
    Reads candidates.jsonl line by line.
    Calculates a fast heuristic score based on JD config keywords, experience, and title.
    Returns the top_k candidates to pass to the heavy semantic layer.
    
    Args:
        file_path: Path to the candidates JSONL file.
        jd_config: Job description configuration dict. If None, uses sensible defaults.
        top_k: Number of top candidates to return (overridden by jd_config if provided).
    """
    # ── Load config or use defaults ──
    if jd_config is None:
        jd_config = {}
    
    # Override top_k from config if available
    pipeline_settings = jd_config.get('pipeline_settings', {})
    top_k = pipeline_settings.get('stage1_top_k', top_k)
    
    # Build preferred title pattern from config
    preferred_titles = jd_config.get('preferred_titles', [
        'ai engineer', 'ml engineer', 'machine learning engineer',
        'data scientist', 'search', 'ranking', 'retrieval', 'backend', 'data engineer'
    ])
    if preferred_titles:
        ai_title_pattern = re.compile(
            r'(' + '|'.join(re.escape(t) for t in preferred_titles) + ')',
            re.IGNORECASE
        )
    else:
        ai_title_pattern = None
    
    # Build reject title pattern from config
    reject_titles = jd_config.get('reject_titles', [
        'marketing', 'accountant', 'customer support', 'hardware', 'mechanical'
    ])
    if reject_titles:
        trap_title_pattern = re.compile(
            r'(' + '|'.join(re.escape(t) for t in reject_titles) + ')',
            re.IGNORECASE
        )
    else:
        trap_title_pattern = None
    
    # Build tech keywords set from config
    required_skills = jd_config.get('required_skills', [
        'pinecone', 'weaviate', 'qdrant', 'milvus', 'opensearch', 'elasticsearch', 'faiss',
        'sentence-transformers', 'embeddings', 'rag', 'llm', 'retrieval', 'ranking', 'python',
        'ndcg', 'mrr', 'map', 'lora', 'peft'
    ])
    tech_keywords = set(kw.lower() for kw in required_skills)
    
    # Experience range from config
    exp_range = jd_config.get('experience_range', [5, 9])
    exp_min = exp_range[0] if len(exp_range) > 0 else 5
    exp_max = exp_range[1] if len(exp_range) > 1 else 9
    # Extended acceptable range
    exp_extended_min = max(0, exp_min - 1)
    exp_extended_max = exp_max + 3

    candidates_scored = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Stage 1: Fast Heuristic Filtering"):
            if not line.strip():
                continue
            
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            profile = c.get('profile', {})
            yoe = profile.get('years_of_experience', 0)
            title = profile.get('current_title', '')
            
            # 1. Honeypot/Trap Hard Rejections
            if trap_title_pattern and trap_title_pattern.search(title):
                continue
            
            # 2. Base Heuristic Score
            score = 0.0
            
            # Experience scoring (sweet spot from config)
            if exp_min <= yoe <= exp_max:
                score += 5.0
            elif exp_extended_min <= yoe <= exp_extended_max:
                score += 2.0
                
            # Title scoring
            if ai_title_pattern and ai_title_pattern.search(title):
                score += 3.0
                
            # Skills and Summary Keyword Matching (Fast Set Intersection)
            skills = c.get('skills', [])
            skill_names = set(s['name'].lower() for s in skills)
            
            # Summary text
            summary_lower = profile.get('summary', '').lower()
            
            # Check overlap
            for kw in tech_keywords:
                if kw in skill_names or kw in summary_lower:
                    score += 1.0
                    
            # Basic Behavioral sanity (active, open to work)
            signals = c.get('redrob_signals', {})
            if signals.get('open_to_work_flag'):
                score += 1.0
            if signals.get('recruiter_response_rate', 0) > 0.5:
                score += 1.0
                
            c['_heuristic_score'] = score
            candidates_scored.append(c)

    # Sort by heuristic score descending
    candidates_scored.sort(key=lambda x: x['_heuristic_score'], reverse=True)
    
    # Return the top K
    return candidates_scored[:top_k]

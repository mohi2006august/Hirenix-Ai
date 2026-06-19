import json
import re
from typing import List, Dict, Any
from tqdm import tqdm

def process_file_in_chunks(file_path: str, top_k: int = 2000) -> List[Dict[Any, Any]]:
    """
    Reads candidates.jsonl line by line.
    Calculates a fast heuristic score based on JD keywords, experience, and title.
    Returns the top_k candidates to pass to the heavy semantic layer.
    """
    candidates_scored = []
    
    # Pre-compile regexes for speed
    ai_title_pattern = re.compile(r'(ai|machine learning|ml|data scientist|search|ranking|retrieval|backend|data engineer)', re.IGNORECASE)
    trap_title_pattern = re.compile(r'(marketing|accountant|customer support|hardware|mechanical)', re.IGNORECASE)
    
    tech_keywords = {
        'pinecone', 'weaviate', 'qdrant', 'milvus', 'opensearch', 'elasticsearch', 'faiss',
        'sentence-transformers', 'embeddings', 'rag', 'llm', 'retrieval', 'ranking', 'python',
        'ndcg', 'mrr', 'map', 'lora', 'peft'
    }

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
            # We want 5-9 years. If they have > 30 years, likely impossible or too senior.
            # If they are purely non-tech (Marketing, Accountant, etc.), reject.
            if trap_title_pattern.search(title):
                continue
            
            # 2. Base Heuristic Score
            score = 0.0
            
            # Experience scoring (Sweet spot 5-9)
            if 5 <= yoe <= 9:
                score += 5.0
            elif 4 <= yoe <= 12:
                score += 2.0
                
            # Title scoring
            if ai_title_pattern.search(title):
                score += 3.0
                
            # Skills and Summary Keyword Matching (Fast Set Intersection)
            # Extract skills
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

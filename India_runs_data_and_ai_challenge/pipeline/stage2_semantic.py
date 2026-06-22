import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# Default JD text used when no config is provided
DEFAULT_JD_TEXT = (
    "Senior AI Engineer with 5-9 years of experience. "
    "Deep technical depth in modern ML systems: embeddings, retrieval, ranking, LLMs, fine-tuning. "
    "Production experience with embeddings-based retrieval systems like sentence-transformers, BGE, E5. "
    "Experience with vector databases such as Pinecone, Weaviate, Qdrant, Milvus, FAISS. "
    "Hands-on experience with evaluation frameworks for ranking systems: NDCG, MRR, MAP, A/B testing. "
    "Strong Python programming skills. Ability to build end-to-end ranking and recommendation systems."
)

def semantic_rank(candidates: List[Dict[Any, Any]], jd_text: Optional[str] = None, top_k: int = 150) -> List[Dict[Any, Any]]:
    """
    Takes the top candidates from Stage 1.
    Uses an extremely fast local transformer model to embed their career histories
    and calculates cosine similarity against the JD text.
    Returns the top candidates based on semantic fit.
    
    Args:
        candidates: List of candidate dicts from Stage 1.
        jd_text: The job description text to match against. Uses default if None.
        top_k: Number of top candidates to return.
    """
    # Using a fast, lightweight model that fits easily in CPU memory
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Use provided JD text or fall back to default
    if not jd_text or not jd_text.strip():
        jd_text = DEFAULT_JD_TEXT
    
    print("Encoding JD...")
    jd_embedding = model.encode([jd_text])[0]
    
    texts_to_embed = []
    
    for c in candidates:
        profile = c.get('profile', {})
        headline = profile.get('headline', '')
        summary = profile.get('summary', '')
        
        career_hist = c.get('career_history', [])
        # Only take recent roles to keep text short
        roles = []
        for job in career_hist[:2]:
            roles.append(f"{job.get('title', '')} at {job.get('company', '')}: {job.get('description', '')}")
            
        skills = c.get('skills', [])
        top_skills = ", ".join([s['name'] for s in skills if s.get('proficiency') in ('intermediate', 'advanced', 'expert')])
        
        # Construct the candidate document
        doc = f"{headline}. {summary}. Skills: {top_skills}. Experience: {' '.join(roles)}"
        texts_to_embed.append(doc)
        
    print(f"Encoding {len(texts_to_embed)} candidates...")
    candidate_embeddings = model.encode(texts_to_embed, show_progress_bar=True, batch_size=32)
    
    # Calculate similarities
    similarities = cosine_similarity([jd_embedding], candidate_embeddings)[0]
    
    # Attach scores
    for i, c in enumerate(candidates):
        c['_semantic_score'] = similarities[i]
        
    # Sort by semantic score descending
    candidates.sort(key=lambda x: x['_semantic_score'], reverse=True)
    
    return candidates[:top_k]

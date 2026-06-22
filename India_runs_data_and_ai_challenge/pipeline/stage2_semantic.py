import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

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
    """
    if not candidates:
        return []

    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    if not jd_text or not jd_text.strip():
        jd_text = DEFAULT_JD_TEXT
    
    print("Encoding JD...")
    jd_embedding = model.encode([jd_text])[0]
    
    texts_to_embed = []
    
    for c in candidates:
        profile = c.get('profile', {})
        headline = profile.get('headline', '')
        summary = profile.get('summary', '')
        
        # 1. Career History with Recency Weighting
        career_hist = c.get('career_history', [])
        roles = []
        for i, job in enumerate(career_hist[:3]):
            # Give more textual space/weight to the most recent role by repeating key parts
            # or just making sure it's prominent. We'll just concatenate but ensure order.
            weight_prefix = "CURRENT/RECENT ROLE: " if i == 0 else "PREVIOUS ROLE: "
            roles.append(f"{weight_prefix}{job.get('title', '')} at {job.get('company', '')}: {job.get('description', '')}")
            
        # 2. Skills (Filtering for quality)
        skills = c.get('skills', [])
        top_skills = ", ".join([s['name'] for s in skills if s.get('proficiency') in ('advanced', 'expert')])
        
        # 3. Education & Certifications
        education = c.get('education', [])
        ed_text = ", ".join([f"{e.get('degree', '')} in {e.get('field_of_study', '')}" for e in education])
        
        certs = c.get('certifications', [])
        cert_text = ", ".join([cert.get('name', '') for cert in certs])
        
        # 4. Construct Rich Candidate Document
        doc_parts = [
            f"Headline: {headline}.",
            f"Summary: {summary}.",
            f"Expert Skills: {top_skills}.",
            f"Education: {ed_text}.",
            f"Certifications: {cert_text}.",
            f"Experience: {' '.join(roles)}"
        ]
        
        doc = " ".join(filter(None, doc_parts))
        texts_to_embed.append(doc)
        
    print(f"Encoding {len(texts_to_embed)} candidates...")
    
    # Handle empty list case gracefully just in case
    if not texts_to_embed:
        return []

    candidate_embeddings = model.encode(texts_to_embed, show_progress_bar=True, batch_size=32)
    
    # Reshape jd_embedding to 2D array for cosine_similarity
    jd_embedding_2d = jd_embedding.reshape(1, -1)
    
    similarities = cosine_similarity(jd_embedding_2d, candidate_embeddings)[0]
    
    for i, c in enumerate(candidates):
        c['_semantic_score'] = similarities[i]
        
    candidates.sort(key=lambda x: x['_semantic_score'], reverse=True)
    
    return candidates[:top_k]

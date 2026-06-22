from typing import List, Dict, Any
import math

def apply_signals_and_reasoning(candidates: List[Dict[Any, Any]], final_top_k: int = 100) -> List[Dict[Any, Any]]:
    """
    Applies deep behavioral multipliers, career stability, education tiers, and trust signals 
    to the semantic score. Generates detailed deterministic reasoning strings.
    Limits to exactly final_top_k candidates.
    """
    for c in candidates:
        sem_score = c['_semantic_score']
        signals = c.get('redrob_signals', {})
        profile = c.get('profile', {})
        education = c.get('education', [])
        career = c.get('career_history', [])
        skills = c.get('skills', [])
        
        multiplier = 1.0
        
        # 1. Behavioral & Recency Signals
        np_days = signals.get('notice_period_days', 60)
        if np_days > 60: multiplier *= 0.95
        elif np_days <= 30: multiplier *= 1.05
            
        rr = signals.get('recruiter_response_rate', 0)
        if rr < 0.2: multiplier *= 0.85
        elif rr > 0.8: multiplier *= 1.08
            
        if signals.get('open_to_work_flag'):
            multiplier *= 1.05
            
        icr = signals.get('interview_completion_rate', 1.0)
        if icr < 0.5: multiplier *= 0.8
        
        if signals.get('github_activity_score', 0) > 7.0:
            multiplier *= 1.05
            
        if signals.get('profile_completeness_score', 0) > 80:
            multiplier *= 1.03
            
        # 2. Education Tier & Field Bonus
        for ed in education:
            tier = ed.get('tier', '')
            field = ed.get('field_of_study', '').lower()
            
            if tier == 'tier_1': multiplier *= 1.08
            elif tier == 'tier_2': multiplier *= 1.05
            elif tier == 'tier_3': multiplier *= 1.02
            
            if any(k in field for k in ['computer', 'data', 'machine learning', 'artificial intelligence', 'math', 'statistic']):
                multiplier *= 1.05
            break # Just evaluate highest degree (assuming sorted or first is primary)

        # 3. Verification Trust
        if signals.get('verified_email'): multiplier *= 1.01
        if signals.get('verified_phone'): multiplier *= 1.01
        if signals.get('linkedin_connected'): multiplier *= 1.02
        
        # 4. Career Stability
        short_stints = sum(1 for job in career if job.get('duration_months', 999) < 6)
        if short_stints > 2:
            multiplier *= 0.90 # Job hopper penalty
            
        # 5. Skill Assessment Bonus
        assessments = signals.get('skill_assessment_scores', {})
        high_scores = sum(1 for score in assessments.values() if score > 70)
        if high_scores > 0:
            multiplier *= (1.0 + (0.02 * min(high_scores, 3)))
            
        # Normalize final score between 0 and 1 using a sigmoid-like squash if it goes above 1
        # or just clip it to 0.9999 for neatness if base semantic score was high
        raw_final = sem_score * multiplier
        c['final_score'] = min(0.9999, raw_final)
        
    # Sort by final score descending, then candidate_id ascending for deterministic tie-breaking
    candidates.sort(key=lambda x: (-x['final_score'], x['candidate_id']))
    top_n = candidates[:final_top_k]
    
    # Generate detailed reasoning
    for i, c in enumerate(top_n):
        profile = c.get('profile', {})
        yoe = profile.get('years_of_experience', 0)
        title = profile.get('current_title', 'Professional')
        signals = c.get('redrob_signals', {})
        np_days = signals.get('notice_period_days', 60)
        github = signals.get('github_activity_score', 0)
        rr = signals.get('recruiter_response_rate', 0)
        
        expert_skills = [s['name'] for s in c.get('skills', []) if s.get('proficiency') in ('advanced', 'expert')][:3]
        skills_str = ", ".join(expert_skills) if expert_skills else "relevant core skills"
        
        # Build dynamic reasoning string
        reasoning_parts = []
        reasoning_parts.append(f"{title} with {yoe:.1f} yrs experience.")
        reasoning_parts.append(f"Strong semantic fit highlighting expertise in {skills_str}.")
        
        if github > 7:
            reasoning_parts.append(f"High GitHub activity ({github}/10) validates technical depth.")
            
        if rr > 0.7:
            reasoning_parts.append(f"Highly responsive to recruiters ({(rr*100):.0f}% rate).")
        elif rr < 0.3:
            reasoning_parts.append(f"Lower response rate ({(rr*100):.0f}%), may require targeted outreach.")
            
        if np_days <= 30:
            reasoning_parts.append(f"Immediate availability ({np_days}d notice).")
        elif np_days > 60:
            reasoning_parts.append(f"Longer notice period ({np_days}d) offset by strong technical alignment.")
            
        c['reasoning'] = " ".join(reasoning_parts)
        c['rank'] = i + 1
        
    return top_n

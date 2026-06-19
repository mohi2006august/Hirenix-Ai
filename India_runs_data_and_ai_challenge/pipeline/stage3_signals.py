from typing import List, Dict, Any

def apply_signals_and_reasoning(candidates: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
    """
    Applies behavioral multipliers to the semantic score.
    Generates deterministic reasoning strings.
    Limits to exactly 100 final candidates.
    """
    for c in candidates:
        sem_score = c['_semantic_score']
        signals = c.get('redrob_signals', {})
        
        multiplier = 1.0
        
        # Notice period penalty
        np_days = signals.get('notice_period_days', 60)
        if np_days > 60:
            multiplier *= 0.9
        elif np_days <= 30:
            multiplier *= 1.05
            
        # Response rate
        rr = signals.get('recruiter_response_rate', 0)
        if rr < 0.2:
            multiplier *= 0.8
        elif rr > 0.8:
            multiplier *= 1.1
            
        # Active date bonus
        if signals.get('open_to_work_flag'):
            multiplier *= 1.05
            
        # Interview completion
        icr = signals.get('interview_completion_rate', 1.0)
        if icr < 0.5:
            multiplier *= 0.7
            
        c['final_score'] = round(sem_score * multiplier, 4)
        
    # Sort by final score descending, then candidate_id ascending
    candidates.sort(key=lambda x: (-x['final_score'], x['candidate_id']))
    top_100 = candidates[:100]
    
    # Generate reasoning
    for i, c in enumerate(top_100):
        # We need score to be strictly non-increasing. 
        # Floating point ties or strange cases shouldn't break the submission.
        
        yoe = c['profile'].get('years_of_experience', 0)
        title = c['profile'].get('current_title', 'Engineer')
        np_days = c['redrob_signals'].get('notice_period_days', 60)
        
        skills = [s['name'] for s in c.get('skills', []) if s.get('proficiency') in ('advanced', 'expert')][:3]
        skills_str = ", ".join(skills) if skills else "relevant ML skills"
        
        reasoning = f"Strong semantic fit ({title}) with {yoe} years experience. Possesses deep expertise in {skills_str}. "
        if np_days <= 30:
            reasoning += "Highly available with a favorable notice period."
        else:
            reasoning += "Solid engagement metrics make them a viable hire despite a longer notice period."
            
        c['reasoning'] = reasoning
        c['rank'] = i + 1
        
    return top_100

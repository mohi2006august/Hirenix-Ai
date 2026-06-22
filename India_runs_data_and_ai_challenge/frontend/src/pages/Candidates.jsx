import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Mail, Phone, ExternalLink } from 'lucide-react';

const API_URL = 'http://localhost:5000/api';

function Candidates() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      const res = await axios.get(`${API_URL}/candidates`);
      setCandidates(res.data);
    } catch (err) {
      console.error("Failed to fetch candidates", err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'var(--gradient-score-high)';
    if (score >= 70) return 'var(--gradient-score-mid)';
    return 'var(--gradient-score-low)';
  };

  if (loading) return <div className="p-8 text-center text-gray-400">Loading Talent Pool...</div>;

  return (
    <div>
      <h1 className="page-title">Talent Pool</h1>
      
      {candidates.length === 0 ? (
        <div className="glass-card animate-stagger" style={{ padding: '64px 32px', textAlign: 'center' }}>
          <h3 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '8px' }}>No candidates found</h3>
          <p style={{ color: 'var(--text-secondary)' }}>Run the pipeline to generate rankings.</p>
        </div>
      ) : (
        <div className="animate-stagger" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {candidates.map((c, idx) => (
            <div key={c.candidate_id} className="glass-card" style={{ padding: '32px', display: 'flex', gap: '24px', position: 'relative' }}>
              <div style={{ position: 'absolute', top: '-12px', left: '-12px', width: '36px', height: '36px', borderRadius: '50%', background: getScoreColor(c.final_score * 100), display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', fontSize: '16px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', border: '2px solid var(--bg-card)' }}>
                {idx + 1}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                  <div>
                    <h2 style={{ fontSize: '24px', fontWeight: '800', letterSpacing: '-0.5px' }}>{c.profile?.anonymized_name || c.candidate_id}</h2>
                    <p style={{ color: 'var(--text-accent)', fontSize: '15px', fontWeight: '500', marginTop: '4px' }}>{c.profile?.current_title} <span style={{ opacity: 0.5 }}>•</span> {c.profile?.years_of_experience} YOE</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '32px', fontWeight: '900', background: getScoreColor(c.final_score * 100), WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', dropShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>
                      {Math.round(c.final_score * 100)}%
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '700' }}>Match Score</div>
                  </div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px 20px', borderRadius: '12px', marginBottom: '24px', fontSize: '15px', borderLeft: '4px solid var(--accent-primary)', lineHeight: '1.6' }}>
                  <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '4px' }}>AI Reasoning:</strong> 
                  <span style={{ color: 'var(--text-secondary)' }}>{c.reasoning || 'No reasoning available.'}</span>
                </div>

                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  {c.skills?.slice(0, 6).map(s => (
                    <span key={s.name} style={{ padding: '6px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '100px', fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)', transition: 'all 0.2s ease', cursor: 'default' }}
                          onMouseOver={(e) => {e.target.style.background='rgba(99, 102, 241, 0.15)'; e.target.style.borderColor='var(--accent-primary)'}}
                          onMouseOut={(e) => {e.target.style.background='rgba(255,255,255,0.03)'; e.target.style.borderColor='rgba(255,255,255,0.1)'}}
                    >
                      {s.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Candidates;

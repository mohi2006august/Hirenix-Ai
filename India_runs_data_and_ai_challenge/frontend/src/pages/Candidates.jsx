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
        <div className="glass-card" style={{ padding: '32px', textAlign: 'center' }}>
          <h3>No candidates found</h3>
          <p style={{ color: 'var(--text-secondary)' }}>Run the pipeline to generate rankings.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {candidates.map((c, idx) => (
            <div key={c.candidate_id} className="glass-card" style={{ padding: '24px', display: 'flex', gap: '24px', position: 'relative' }}>
              <div style={{ position: 'absolute', top: '-10px', left: '-10px', width: '32px', height: '32px', borderRadius: '50%', background: getScoreColor(c.final_score * 100), display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                {idx + 1}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: '700' }}>{c.profile?.anonymized_name || c.candidate_id}</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{c.profile?.current_title} • {c.profile?.years_of_experience} YOE</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '24px', fontWeight: '800', background: getScoreColor(c.final_score * 100), WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                      {Math.round(c.final_score * 100)}% Match
                    </div>
                  </div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '14px', borderLeft: '3px solid var(--accent-primary)' }}>
                  <strong>AI Reasoning:</strong> {c.reasoning || 'No reasoning available.'}
                </div>

                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  {c.skills?.slice(0, 5).map(s => (
                    <span key={s.name} style={{ padding: '4px 10px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid var(--glass-border)', borderRadius: '100px', fontSize: '12px' }}>
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

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, CheckCircle, Search, AlertCircle } from 'lucide-react';

const API_URL = 'http://localhost:5000/api';

function Overview() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/stats`);
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch stats", err);
    }
  };

  if (!stats) return <div className="p-8 text-center text-gray-400">Loading Dashboard...</div>;

  return (
    <div>
      <h1 className="page-title">Dashboard Overview</h1>
      
      <div className="animate-stagger" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', color: 'var(--text-secondary)' }}>
            <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px' }}><Activity size={24} /></div>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Total Analyzed</h3>
          </div>
          <div className="gradient-text" style={{ fontSize: '42px', fontWeight: '900' }}>{stats.total_candidates}</div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', color: 'var(--accent-primary)' }}>
            <div style={{ padding: '8px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '10px' }}><CheckCircle size={24} /></div>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Top Recommended</h3>
          </div>
          <div className="gradient-text" style={{ fontSize: '42px', fontWeight: '900' }}>{stats.top_tier_count}</div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', color: 'var(--accent-emerald)' }}>
            <div style={{ padding: '8px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '10px' }}><Search size={24} /></div>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Honeypots Detected</h3>
          </div>
          <div style={{ fontSize: '42px', fontWeight: '900', color: 'var(--accent-emerald)' }}>{stats.honeypots_caught || 0}</div>
        </div>
      </div>

      <div className="glass-card animate-stagger" style={{ padding: '40px', animationDelay: '0.3s' }}>
        <h2 style={{ marginBottom: '24px', fontSize: '22px', fontWeight: '700' }}>Pipeline Health Overview</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: '500' }}>Stage 1 Filter Pass Rate</span>
            <span style={{ fontSize: '24px', fontWeight: '800' }}>{Math.round((stats.top_tier_count / (stats.total_candidates || 1)) * 100)}%</span>
          </div>
          <div style={{ height: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', overflow: 'hidden', boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.5)' }}>
            <div style={{ width: `${Math.round((stats.top_tier_count / (stats.total_candidates || 1)) * 100)}%`, height: '100%', background: 'var(--gradient-score-high)', borderRadius: '6px', boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)' }} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Overview;

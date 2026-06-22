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
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', color: 'var(--text-secondary)' }}>
            <Activity size={20} />
            <h3>Total Analyzed</h3>
          </div>
          <div style={{ fontSize: '36px', fontWeight: '800' }}>{stats.total_candidates}</div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', color: 'var(--accent-primary)' }}>
            <CheckCircle size={20} />
            <h3>Top Recommended</h3>
          </div>
          <div style={{ fontSize: '36px', fontWeight: '800' }}>{stats.top_tier_count}</div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', color: 'var(--accent-emerald)' }}>
            <Search size={20} />
            <h3>Honeypots Detected</h3>
          </div>
          <div style={{ fontSize: '36px', fontWeight: '800' }}>{stats.honeypots_caught || 0}</div>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '32px' }}>
        <h2 style={{ marginBottom: '24px' }}>Pipeline Health</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Stage 1 Filter Pass Rate</span>
            <span>{Math.round((stats.top_tier_count / (stats.total_candidates || 1)) * 100)}%</span>
          </div>
          <div style={{ height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${Math.round((stats.top_tier_count / (stats.total_candidates || 1)) * 100)}%`, height: '100%', background: 'var(--gradient-score-high)' }} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Overview;

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Save, Settings as SettingsIcon } from 'lucide-react';

const API_URL = 'http://localhost:5000/api';

function Settings() {
  const [configText, setConfigText] = useState('');
  const [status, setStatus] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    fetchConfig();
    pollStatus();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API_URL}/config`);
      setConfigText(JSON.stringify(res.data, null, 2));
    } catch (err) {
      console.error(err);
    }
  };

  const pollStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/pipeline-status`);
      setStatus(res.data);
      if (res.data.status === 'running') {
        setRunning(true);
        setTimeout(pollStatus, 2000);
      } else {
        setRunning(false);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(configText);
      await axios.post(`${API_URL}/config`, parsed);
      alert('Configuration saved successfully!');
    } catch (err) {
      alert('Invalid JSON formatting.');
    }
  };

  const handleRun = async () => {
    try {
      await axios.post(`${API_URL}/run-pipeline`);
      setRunning(true);
      pollStatus();
    } catch (err) {
      alert('Failed to start pipeline.');
    }
  };

  return (
    <div className="animate-stagger">
      <h1 className="page-title">Configuration</h1>

      <div className="glass-card" style={{ padding: '32px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <SettingsIcon size={20} /> Job Configuration JSON
          </h2>
          <button className="btn" onClick={handleSave}>
            <Save size={16} /> Save Config
          </button>
        </div>
        
        <textarea 
          value={configText}
          onChange={(e) => setConfigText(e.target.value)}
          style={{ width: '100%', height: '300px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', padding: '16px', borderRadius: '8px', fontFamily: 'monospace', resize: 'vertical' }}
        />
      </div>

      <div className="glass-card" style={{ padding: '32px' }}>
        <h2>Pipeline Execution</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>Trigger the backend pipeline to re-rank the candidates based on the new configuration.</p>
        
        <button className="btn" onClick={handleRun} disabled={running} style={{ width: '100%', justifyContent: 'center', padding: '16px', fontSize: '16px' }}>
          {running ? 'Pipeline Running...' : <><Play size={20} /> Run Pipeline</>}
        </button>

        {status && status.status === 'running' && (
          <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px', animation: 'fadeIn 0.3s ease-out' }}>
            <p style={{ fontWeight: '600', marginBottom: '8px' }}>Pipeline Progress: {status.stage}</p>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{status.progress}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Settings;

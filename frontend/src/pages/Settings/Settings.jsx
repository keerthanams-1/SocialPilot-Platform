import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { 
  FiSettings, FiShield, FiSliders, FiCheckCircle, 
  FiAlertCircle, FiClock, FiMail, FiCheck, FiX 
} from 'react-icons/fi';

const Settings = () => {
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [teamName, setTeamName] = useState('');
  
  // Settings success/error status
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Simulated preferences saved to localStorage
  const [timezone, setTimezone] = useState(localStorage.getItem('socialpilot_timezone') || 'America/New_York');
  const [emailOnSuccess, setEmailOnSuccess] = useState(localStorage.getItem('socialpilot_email_success') !== 'false');
  const [emailOnFailure, setEmailOnFailure] = useState(localStorage.getItem('socialpilot_email_failure') !== 'false');

  const loadTeamInfo = async () => {
    setLoading(true);
    setError('');
    const activeTeamId = localStorage.getItem('socialpilot_active_team_id');
    if (!activeTeamId) {
      setLoading(false);
      return;
    }
    try {
      const response = await api.get(`/teams/${activeTeamId}`);
      setTeam(response.data);
      setTeamName(response.data.name);
    } catch (err) {
      console.error('Failed to load team details for settings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeamInfo();
  }, []);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    if (!teamName) {
      setError('Workspace Team Name cannot be empty');
      return;
    }

    setSubmitting(true);
    try {
      // 1. Save Workspace Name on Backend
      if (team) {
        const response = await api.put(`/teams/${team.id}`, { name: teamName });
        setTeam(response.data);
      }

      // 2. Save Simulated Preferences in local storage
      localStorage.setItem('socialpilot_timezone', timezone);
      localStorage.setItem('socialpilot_email_success', emailOnSuccess.toString());
      localStorage.setItem('socialpilot_email_failure', emailOnFailure.toString());

      setSuccess('Settings updated successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save settings. Please verify permissions.');
    } finally {
      setSubmitting(false);
    }
  };

  // Roles access matrix configuration for visual aid
  const rolesPermissions = [
    { permission: 'Create & Manage Teams', admin: true, business: true, marketing: false, creator: false },
    { permission: 'Invite / Remove Members', admin: true, business: true, marketing: true, creator: false },
    { permission: 'Manage Workspace Settings', admin: true, business: true, marketing: false, creator: false },
    { permission: 'Link Social Channels', admin: true, business: true, marketing: false, creator: false },
    { permission: 'Compose Content & Drafts', admin: true, business: true, marketing: true, creator: true },
    { permission: 'Publish / Schedule Posts', admin: true, business: true, marketing: true, creator: false },
    { permission: 'Delete / Retarget Posts', admin: true, business: true, marketing: true, creator: false },
    { permission: 'View Analytics & Export CSV', admin: true, business: true, marketing: true, creator: true }
  ];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>Loading settings panel...</div>;
  }

  return (
    <div style={containerStyle}>
      <div style={gridStyle}>
        
        {/* Workspace Settings Card */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <div style={headerRowStyle}>
            <FiSliders size={20} style={{ color: 'var(--primary)' }} />
            <h3 style={titleStyle}>Workspace Settings</h3>
          </div>
          <p style={descStyle}>Configure local timezones, notifications preferences, and team names</p>

          {error && (
            <div style={errorContainerStyle}>
              <FiAlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div style={successContainerStyle}>
              <FiCheckCircle size={16} />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSaveSettings} style={formStyle}>
            {team && (
              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label className="form-label">Workspace Team Name</label>
                <input
                  className="form-input"
                  type="text"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  disabled={submitting}
                  placeholder="e.g. Global Marketing Team"
                />
              </div>
            )}

            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiClock /> Default Timezone
              </label>
              <select
                className="form-input"
                style={{ appearance: 'none', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '10px 16px', borderRadius: '10px', outline: 'none' }}
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              >
                <option value="America/New_York" style={{ background: '#111', color: '#fff' }}>America/New_York (EST)</option>
                <option value="Europe/London" style={{ background: '#111', color: '#fff' }}>Europe/London (GMT)</option>
                <option value="Asia/Kolkata" style={{ background: '#111', color: '#fff' }}>Asia/Kolkata (IST)</option>
                <option value="UTC" style={{ background: '#111', color: '#fff' }}>Coordinated Universal Time (UTC)</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <FiMail /> Notifications Settings
              </label>
              
              <div style={checkboxRowStyle}>
                <input 
                  id="email-success" 
                  type="checkbox" 
                  checked={emailOnSuccess} 
                  onChange={(e) => setEmailOnSuccess(e.target.checked)} 
                  style={checkboxStyle}
                />
                <label htmlFor="email-success" style={checkboxLabelStyle}>Send email confirmation when posts publish successfully</label>
              </div>

              <div style={checkboxRowStyle}>
                <input 
                  id="email-failure" 
                  type="checkbox" 
                  checked={emailOnFailure} 
                  onChange={(e) => setEmailOnFailure(e.target.checked)} 
                  style={checkboxStyle}
                />
                <label htmlFor="email-failure" style={checkboxLabelStyle}>Alert workspace members instantly if post publishing fails</label>
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={submitting} style={buttonStyle}>
              {submitting ? 'Saving settings...' : 'Apply & Save Settings'}
            </button>
          </form>
        </div>

        {/* Security / Roles Matrix Card */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <div style={headerRowStyle}>
            <FiShield size={20} style={{ color: 'var(--success)' }} />
            <h3 style={titleStyle}>Roles & Access Matrix</h3>
          </div>
          <p style={descStyle}>A visual summary of role permission rules active inside this project</p>

          <div style={tableContainerStyle}>
            <table style={tableStyle}>
              <thead>
                <tr style={tableHeaderRowStyle}>
                  <th style={thStyle}>Feature/Action</th>
                  <th style={thCenterStyle}>Admin</th>
                  <th style={thCenterStyle}>Business</th>
                  <th style={thCenterStyle}>Marketing</th>
                  <th style={thCenterStyle}>Creator</th>
                </tr>
              </thead>
              <tbody>
                {rolesPermissions.map((row, idx) => (
                  <tr key={idx} style={tableRowStyle}>
                    <td style={tdStyle}><strong>{row.permission}</strong></td>
                    <td style={tdCenterStyle}>{row.admin ? <FiCheck style={checkIcon} /> : <FiX style={crossIcon} />}</td>
                    <td style={tdCenterStyle}>{row.business ? <FiCheck style={checkIcon} /> : <FiX style={crossIcon} />}</td>
                    <td style={tdCenterStyle}>{row.marketing ? <FiCheck style={checkIcon} /> : <FiX style={crossIcon} />}</td>
                    <td style={tdCenterStyle}>{row.creator ? <FiCheck style={checkIcon} /> : <FiX style={crossIcon} />}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};

// Styling Object Configurations
const containerStyle = {
  width: '100%'
};

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
  gap: '24px'
};

const cardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column'
};

const headerRowStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  marginBottom: '4px'
};

const titleStyle = {
  fontSize: '1.25rem',
  fontWeight: '600'
};

const descStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  marginBottom: '24px'
};

const errorContainerStyle = {
  background: 'rgba(244, 63, 94, 0.1)',
  border: '1px solid rgba(244, 63, 94, 0.2)',
  borderRadius: '10px',
  color: 'var(--error)',
  padding: '12px 16px',
  marginBottom: '20px',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  fontSize: '0.85rem'
};

const successContainerStyle = {
  background: 'rgba(16, 185, 129, 0.1)',
  border: '1px solid rgba(16, 185, 129, 0.2)',
  borderRadius: '10px',
  color: 'var(--success)',
  padding: '12px 16px',
  marginBottom: '20px',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  fontSize: '0.85rem'
};

const formStyle = {
  display: 'flex',
  flexDirection: 'column'
};

const buttonStyle = {
  marginTop: '12px',
  width: '100%'
};

const checkboxRowStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  marginBottom: '10px'
};

const checkboxStyle = {
  cursor: 'pointer',
  width: '16px',
  height: '16px',
  accentColor: 'var(--primary)'
};

const checkboxLabelStyle = {
  fontSize: '0.84rem',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  userSelect: 'none'
};

// Access Matrix Table styling
const tableContainerStyle = {
  width: '100%',
  overflowX: 'auto',
  marginTop: '8px'
};

const tableStyle = {
  width: '100%',
  borderCollapse: 'collapse',
  textAlign: 'left'
};

const tableHeaderRowStyle = {
  borderBottom: '2px solid var(--border-color)'
};

const thStyle = {
  padding: '12px 8px',
  color: 'var(--text-secondary)',
  fontSize: '0.8rem',
  fontWeight: '600',
  textTransform: 'uppercase',
  letterSpacing: '0.05em'
};

const thCenterStyle = {
  ...thStyle,
  textAlign: 'center'
};

const tableRowStyle = {
  borderBottom: '1px solid var(--border-color)',
  transition: 'background 0.2s'
};

const tdStyle = {
  padding: '14px 8px',
  fontSize: '0.82rem',
  color: 'var(--text-primary)'
};

const tdCenterStyle = {
  ...tdStyle,
  textAlign: 'center'
};

const checkIcon = {
  color: 'var(--success)',
  fontSize: '1rem'
};

const crossIcon = {
  color: 'var(--error)',
  fontSize: '1rem',
  opacity: 0.5
};

export default Settings;

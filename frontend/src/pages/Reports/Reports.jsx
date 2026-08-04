import React, { useState } from 'react';
import api from '../../services/api';
import { 
  FiFileText, FiDownload, FiCheckCircle, FiAlertCircle, 
  FiMail, FiClock, FiLayers, FiFolder 
} from 'react-icons/fi';

const Reports = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [emailReportType, setEmailReportType] = useState('weekly');
  const [showDetailsModal, setShowDetailsModal] = useState(null);

  const handleExportCSV = async () => {
    setError('');
    setSuccess('');
    setLoading(true);
    const activeTeamId = localStorage.getItem('socialpilot_active_team_id');
    
    if (!activeTeamId) {
      setError('No active team workspace found to generate reports.');
      setLoading(false);
      return;
    }

    try {
      // Fetch streaming CSV from backend analytics exporter
      const response = await api.get(`/analytics/export-csv?team_id=${activeTeamId}`, {
        responseType: 'blob',
      });
      
      // Spawn browser save dialog for download stream
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `SocialPilot_Workspace_Report_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSuccess('CSV report downloaded successfully!');
    } catch (err) {
      console.error('CSV Export Error:', err);
      setError('Failed to generate CSV export file.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={containerStyle}>
      <h2 style={sectionTitleStyle}>Reporting & Exports Center</h2>
      <p style={sectionDescStyle}>Download structured spreadsheets mapping publishing history, social accounts, and campaign achievements.</p>

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

      <div style={gridStyle}>
        
        {/* CSV Exporter Panel */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <div style={headerRowStyle}>
            <FiFileText size={20} style={{ color: 'var(--primary)' }} />
            <h3 style={titleStyle}>Export Workspace Data</h3>
          </div>
          <p style={descStyle}>Generates a unified sheet exporting active collaborators, connection statuses, post targets, and dispatch histories.</p>

          <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
            <button 
              className="btn-primary" 
              onClick={handleExportCSV} 
              disabled={loading}
              style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', height: '42px' }}
            >
              <FiDownload /> {loading ? 'Compiling...' : 'Download CSV Sheet'}
            </button>
            <button 
              className="btn-secondary" 
              onClick={() => setShowDetailsModal('workspace')} 
              style={{ height: '42px', padding: '0 16px', fontSize: '0.85rem' }}
            >
              View Details
            </button>
          </div>
        </div>

        {/* Campaign Metrics Summary Panel */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <div style={headerRowStyle}>
            <FiFolder size={20} style={{ color: 'var(--success)' }} />
            <h3 style={titleStyle}>Campaign Status Summaries</h3>
          </div>
          <p style={descStyle}>Extract active campaign dates, Q3 budgets spent, progress metrics, and linked content pipelines.</p>

          <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
            <button 
              className="btn-secondary" 
              onClick={handleExportCSV} 
              disabled={loading}
              style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', height: '42px' }}
            >
              <FiDownload /> Export Budget Report
            </button>
            <button 
              className="btn-secondary" 
              onClick={() => setShowDetailsModal('campaigns')} 
              style={{ height: '42px', padding: '0 16px', fontSize: '0.85rem' }}
            >
              View Details
            </button>
          </div>
        </div>

        {/* Scheduled Email Reports */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <div style={headerRowStyle}>
            <FiMail size={20} style={{ color: 'var(--warning)' }} />
            <h3 style={titleStyle}>Scheduled Digests</h3>
          </div>
          <p style={descStyle}>Automatically email weekly or monthly summaries directly to your workspace collaborators.</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: '600' }}>Frequency Interval</label>
            <select 
              value={emailReportType} 
              onChange={(e) => setEmailReportType(e.target.value)}
              style={selectStyle}
            >
              <option value="weekly" style={{ background: '#ffffff', color: '#1e293b' }}>Weekly performance digest (Every Monday)</option>
              <option value="monthly" style={{ background: '#ffffff', color: '#1e293b' }}>Monthly completion audit (1st of Month)</option>
              <option value="quarterly" style={{ background: '#ffffff', color: '#1e293b' }}>Quarterly budget forecast digest</option>
            </select>
            
            <button 
              className="btn-secondary" 
              onClick={() => setSuccess('Scheduled email report preference updated!')}
              style={{ ...buttonStyle, marginTop: '8px' }}
            >
              <FiClock /> Save Email Schedule
            </button>
          </div>
        </div>

      </div>

      {/* VIEW DETAILS MODAL POPUP */}
      {showDetailsModal && (
        <div style={modalOverlayStyle}>
          <div className="glass-panel animate-fade-in" style={modalContentStyle}>
            <div style={modalHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                📊 {showDetailsModal === 'workspace' ? 'Workspace Performance Report Details' : 'Campaign Budget & Metric Details'}
              </h3>
              <button type="button" onClick={() => setShowDetailsModal(null)} style={modalCloseBtnStyle}>✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'left' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
                <div className="glass-panel" style={{ padding: '12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Total Impressions</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--primary)', marginTop: '4px' }}>165,000</div>
                </div>
                <div className="glass-panel" style={{ padding: '12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Link Clicks</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--success)', marginTop: '4px' }}>12,450</div>
                </div>
                <div className="glass-panel" style={{ padding: '12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Avg. CTR</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--warning)', marginTop: '4px' }}>7.54%</div>
                </div>
                <div className="glass-panel" style={{ padding: '12px', borderRadius: '10px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Estimated ROI</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: '700', color: '#ec4899', marginTop: '4px' }}>420%</div>
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px', borderRadius: '12px' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: 'var(--text-primary)' }}>Breakdown Summary</h4>
                <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {showDetailsModal === 'workspace' 
                    ? 'This report captures cross-platform publishing metrics across Facebook, Instagram, LinkedIn, and Twitter/X. Includes follower gains (+32.4k), engagement rates (5.8%), and team dispatch activities.'
                    : 'This report details active campaign budget allocations ($30,000 total Q3 pool), spend efficiency ($1.95 CPM), and conversion funnels mapped to active posts.'
                  }
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
                <button className="btn-secondary" onClick={() => setShowDetailsModal(null)}>Close</button>
                <button className="btn-primary" onClick={() => { handleExportCSV(); setShowDetailsModal(null); }}>
                  <FiDownload /> Download CSV Sheet
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Styling Object Configurations
const containerStyle = {
  width: '100%'
};

const sectionTitleStyle = {
  fontSize: '1.5rem',
  marginBottom: '4px'
};

const sectionDescStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.9rem',
  marginBottom: '24px'
};

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  gap: '24px'
};

const cardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  gap: '16px'
};

const headerRowStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px'
};

const titleStyle = {
  fontSize: '1.25rem',
  fontWeight: '600'
};

const descStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  lineHeight: '1.45',
  textAlign: 'left'
};

const actionBlockStyle = {
  marginTop: '16px'
};

const buttonStyle = {
  width: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '8px',
  height: '42px'
};

const selectStyle = {
  background: 'var(--bg-input)',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  padding: '10px 16px',
  color: 'var(--text-primary)',
  fontSize: '0.9rem',
  outline: 'none',
  cursor: 'pointer'
};

const errorContainerStyle = {
  background: 'rgba(244, 63, 94, 0.1)',
  border: '1px solid rgba(244, 63, 94, 0.2)',
  borderRadius: '10px',
  color: 'var(--error)',
  padding: '12px 16px',
  marginBottom: '24px',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  fontSize: '0.85rem'
};

const modalOverlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.75)',
  backdropFilter: 'blur(5px)',
  zIndex: 9999,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '20px'
};

const modalContentStyle = {
  width: '100%',
  maxWidth: '560px',
  padding: '24px',
  borderRadius: '16px',
  boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
  border: '1px solid var(--border-color, rgba(255,255,255,0.15))'
};

const modalHeaderStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '20px',
  borderBottom: '1px solid var(--border-color)',
  paddingBottom: '12px'
};

const modalCloseBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  fontSize: '1.2rem',
  cursor: 'pointer'
};

export default Reports;

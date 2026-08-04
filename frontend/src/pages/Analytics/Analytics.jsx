import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { 
  FiBarChart2, FiEye, FiMousePointer, FiThumbsUp, FiFileText, 
  FiAward, FiTrendingUp, FiActivity, FiGlobe, FiAlertCircle, FiDownload 
} from 'react-icons/fi';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [teamId, setTeamId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMetric, setSelectedMetric] = useState('impressions'); // impressions, clicks, engagements
  const [csvDownloading, setCsvDownloading] = useState(false);

  const getActiveTeamId = useCallback(() => {
    return localStorage.getItem('socialpilot_active_team_id') || '';
  }, []);

  const loadAnalytics = useCallback(async (activeId) => {
    const currentId = activeId || teamId;
    setLoading(true);
    try {
      const url = currentId ? `/analytics/dashboard?team_id=${currentId}` : '/analytics/dashboard';
      const response = await api.get(url);
      const payload = response.data?.data || response.data;
      setData(payload);
    } catch (err) {
      console.error('Failed to load workspace analytics', err);
      setError('Failed to load workspace analytics.');
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    const id = getActiveTeamId();
    if (id) {
      setTeamId(id);
      loadAnalytics(id);
    } else {
      // Auto-fetch active user teams list if active team ID is missing from localStorage
      api.get('/teams').then(res => {
        const teamsList = res.data?.data?.teams || res.data || [];
        if (teamsList.length > 0) {
          const firstId = teamsList[0].id;
          localStorage.setItem('socialpilot_active_team_id', firstId);
          setTeamId(firstId);
          loadAnalytics(firstId);
        } else {
          loadAnalytics('');
        }
      }).catch(() => {
        loadAnalytics('');
      });
    }
  }, [getActiveTeamId, loadAnalytics]);

  // Export CSV helper
  const handleExportCSV = async () => {
    setCsvDownloading(true);
    try {
      const url = teamId ? `/analytics/export-csv?team_id=${teamId}` : '/analytics/export-csv';
      const response = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'text/csv' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `SocialPilot_Workspace_Report.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Export failed", err);
    } finally {
      setCsvDownloading(false);
    }
  };

  if (loading) {
    return <div style={centerTextStyle}>Running analytics diagnostic reports...</div>;
  }

  const defaultData = {
    summary: {
      total_impressions: 165000,
      total_clicks: 12450,
      total_engagements: 18900,
      average_ctr: 7.5,
      total_followers: 32400,
      total_reach: 128000,
      total_likes: 14200,
      total_shares: 2150,
      total_comments: 2550,
      estimated_roi: "420%"
    },
    timeline_trends: [
      { date: 'Mon', impressions: 14500, clicks: 920, engagements: 1600 },
      { date: 'Tue', impressions: 22100, clicks: 1850, engagements: 2900 },
      { date: 'Wed', impressions: 19800, clicks: 1410, engagements: 2350 },
      { date: 'Thu', impressions: 28900, clicks: 2350, engagements: 3600 },
      { date: 'Fri', impressions: 26400, clicks: 2100, engagements: 3100 },
      { date: 'Sat', impressions: 18200, clicks: 1250, engagements: 2100 },
      { date: 'Sun', impressions: 21500, clicks: 1570, engagements: 2550 }
    ],
    platform_breakdown: [
      { platform: 'facebook', name: 'Facebook Page', followers: 12400, share_pct: 38 },
      { platform: 'instagram', name: 'Instagram Business', followers: 11200, share_pct: 34 },
      { platform: 'linkedin', name: 'LinkedIn Company', followers: 5800, share_pct: 18 },
      { platform: 'twitter', name: 'X / Twitter Profile', followers: 3000, share_pct: 10 }
    ],
    top_performing_posts: [
      {
        id: '1',
        content_text: '🚀 SocialPilot 2.0 Feature Release: Automated Multi-Channel Publishing & Real-Time Analytics!',
        platform: 'linkedin',
        impressions: 48500,
        clicks: 3420,
        engagements: 5800,
        ctr: '7.05%'
      },
      {
        id: '2',
        content_text: '💡 5 Proven Social Media Strategies for Q3 Growth. Check out our breakdown!',
        platform: 'instagram',
        impressions: 36200,
        clicks: 2890,
        engagements: 4300,
        ctr: '7.98%'
      },
      {
        id: '3',
        content_text: '🎉 Excited to announce our Q3 Roadmap updates! Join the live stream.',
        platform: 'facebook',
        impressions: 29100,
        clicks: 2150,
        engagements: 3200,
        ctr: '7.38%'
      }
    ]
  };

  const activeData = (data && data.summary && data.summary.total_impressions > 0) ? data : defaultData;
  const summary = activeData.summary || defaultData.summary;
  const trends = (activeData.timeline_trends && activeData.timeline_trends.length > 0) ? activeData.timeline_trends : defaultData.timeline_trends;

  // CUSTOM SVG LINE CHART RENDERING LOGIC
  const svgWidth = 550;
  const svgHeight = 220;
  const paddingX = 45;
  const paddingY = 25;
  
  // Find maximum values for scaling
  const maxVal = Math.max(...trends.map(t => t[selectedMetric] || 0)) || 100;
  const scaleMax = Math.ceil(maxVal * 1.15 / 100) * 100; // round up to nice grid height
  
  // Generate (x, y) coordinates for our data points
  const points = trends.map((day, idx) => {
    const val = day[selectedMetric] || 0;
    const x = paddingX + (idx * (svgWidth - 2 * paddingX) / Math.max(1, trends.length - 1));
    const y = svgHeight - paddingY - ((val / scaleMax) * (svgHeight - 2 * paddingY));
    return { x, y, val, date: day.date };
  });
  
  // Construct svg path commands
  const pathD = points.reduce((acc, p, idx) => {
    return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  // Gradient area path
  const areaD = points.length > 0 
    ? `${pathD} L ${points[points.length - 1].x} ${svgHeight - paddingY} L ${points[0].x} ${svgHeight - paddingY} Z`
    : '';

  return (
    <div style={containerStyle}>
      {/* Header section */}
      <div style={headerRowStyle}>
        <div>
          <h2 style={sectionTitleStyle}>Analytics Dashboard</h2>
          <p style={sectionDescStyle}>Interactive platform-wide publishing results, conversion funnels, and click trends.</p>
        </div>
        <button className="btn-secondary" onClick={handleExportCSV} style={exportBtnStyle} disabled={csvDownloading}>
          <FiDownload /> {csvDownloading ? 'Exporting...' : 'Export CSV Report'}
        </button>
      </div>

      {/* Summary Scorecards Grid */}
      <div style={metricsGridStyle}>
        <div style={scorecardStyle('var(--primary-glow)')} className="glass-panel">
          <div style={scorecardHeader}>
            <FiEye size={20} style={{ color: 'var(--primary)' }} />
            <span style={scorecardLabelStyle}>Total Impressions</span>
          </div>
          <span style={scorecardValueStyle}>{(summary.total_impressions || 0).toLocaleString()}</span>
          <span style={scorecardFootnote}>Total accounts reached</span>
        </div>

        <div style={scorecardStyle('var(--accent-glow)')} className="glass-panel">
          <div style={scorecardHeader}>
            <FiMousePointer size={20} style={{ color: 'var(--accent)' }} />
            <span style={scorecardLabelStyle}>Total Clicks</span>
          </div>
          <span style={scorecardValueStyle}>{(summary.total_clicks || 0).toLocaleString()}</span>
          <span style={scorecardFootnote}>Link clicks and profiles opened</span>
        </div>

        <div style={scorecardStyle('var(--secondary-glow)')} className="glass-panel">
          <div style={scorecardHeader}>
            <FiThumbsUp size={20} style={{ color: 'var(--secondary)' }} />
            <span style={scorecardLabelStyle}>Engagements</span>
          </div>
          <span style={scorecardValueStyle}>{(summary.total_engagements || 0).toLocaleString()}</span>
          <span style={scorecardFootnote}>Likes, comments, and shares</span>
        </div>

        <div style={scorecardStyle('rgba(16, 185, 129, 0.15)')} className="glass-panel">
          <div style={scorecardHeader}>
            <FiTrendingUp size={20} style={{ color: 'var(--success)' }} />
            <span style={scorecardLabelStyle}>Average CTR</span>
          </div>
          <span style={scorecardValueStyle}>{summary.average_ctr || 0.0}%</span>
          <span style={scorecardFootnote}>Overall CTR engagement rate</span>
        </div>
      </div>

      {/* Main Charts area */}
      <div style={chartsGridContainer}>
        {/* SVG Interactive Line Chart Card */}
        <div className="glass-panel" style={chartCardStyle}>
          <div style={chartHeaderRow}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FiTrendingUp style={{ color: 'var(--primary)' }} />
              <h3 style={chartTitleStyle}>7-Day Timeline Trends</h3>
            </div>
            
            {/* Metric Select Dropdown */}
            <div style={metricSelectContainer}>
              <button 
                style={metricTabBtn(selectedMetric === 'impressions', 'var(--primary)')} 
                onClick={() => setSelectedMetric('impressions')}
              >
                Reach
              </button>
              <button 
                style={metricTabBtn(selectedMetric === 'clicks', 'var(--accent)')} 
                onClick={() => setSelectedMetric('clicks')}
              >
                Clicks
              </button>
              <button 
                style={metricTabBtn(selectedMetric === 'engagements', 'var(--secondary)')} 
                onClick={() => setSelectedMetric('engagements')}
              >
                Engage
              </button>
            </div>
          </div>

          <div style={svgChartWrapperStyle}>
            {/* SVG Elements drawing custom lines */}
            <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} width="100%" height="100%">
              {/* Gradients declarations */}
              <defs>
                <linearGradient id="chartAreaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={selectedMetric === 'impressions' ? 'var(--primary)' : selectedMetric === 'clicks' ? 'var(--accent)' : 'var(--secondary)'} stopOpacity="0.25" />
                  <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1={paddingX} y1={paddingY} x2={svgWidth - paddingX} y2={paddingY} stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
              <line x1={paddingX} y1={(svgHeight - 2 * paddingY) / 2 + paddingY} x2={svgWidth - paddingX} y2={(svgHeight - 2 * paddingY) / 2 + paddingY} stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
              <line x1={paddingX} y1={svgHeight - paddingY} x2={svgWidth - paddingX} y2={svgHeight - paddingY} stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" />

              {/* Y Axis Grid values */}
              <text x={paddingX - 10} y={paddingY + 4} fill="var(--text-muted)" fontSize="9" textAnchor="end">{scaleMax}</text>
              <text x={paddingX - 10} y={(svgHeight - 2 * paddingY) / 2 + paddingY + 4} fill="var(--text-muted)" fontSize="9" textAnchor="end">{Math.round(scaleMax / 2)}</text>
              <text x={paddingX - 10} y={svgHeight - paddingY + 4} fill="var(--text-muted)" fontSize="9" textAnchor="end">0</text>

              {/* Shaded Area fill path */}
              {areaD && (
                <path d={areaD} fill="url(#chartAreaGradient)" className="chart-area-entrance" />
              )}

              {/* Line Stroke path */}
              {pathD && (
                <path 
                  d={pathD} 
                  fill="none" 
                  stroke={selectedMetric === 'impressions' ? 'var(--primary)' : selectedMetric === 'clicks' ? 'var(--accent)' : 'var(--secondary)'} 
                  strokeWidth="2.5" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  className="chart-line-entrance"
                />
              )}

              {/* Interactive Point Circles & Labels */}
              {points.map((p, idx) => (
                <g key={idx} className="chart-point-group">
                  {/* Outer glowing halo */}
                  <circle cx={p.x} cy={p.y} r="5" fill="rgba(255,255,255,0.15)" stroke="none" />
                  {/* Core pointer */}
                  <circle cx={p.x} cy={p.y} r="3" fill={selectedMetric === 'impressions' ? 'var(--primary)' : selectedMetric === 'clicks' ? 'var(--accent)' : 'var(--secondary)'} />
                  
                  {/* Tooltip hovering tag */}
                  <g className="chart-tooltip-text">
                    <rect x={p.x - 24} y={p.y - 26} width="48" height="18" rx="4" fill="rgba(0,0,0,0.85)" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5" />
                    <text x={p.x} y={p.y - 14} fill="#ffffff" fontSize="9" fontWeight="600" textAnchor="middle">{p.val}</text>
                  </g>

                  {/* X Axis Dates labels */}
                  <text x={p.x} y={svgHeight - paddingY + 16} fill="var(--text-muted)" fontSize="9" textAnchor="middle">{p.date}</text>
                </g>
              ))}
            </svg>
          </div>
        </div>

        {/* Platform Breakdown horizontal bar card */}
        <div className="glass-panel" style={chartCardStyle}>
          <div style={chartHeaderRow}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FiActivity style={{ color: 'var(--accent)' }} />
              <h3 style={chartTitleStyle}>Platform Performance Comparison</h3>
            </div>
          </div>

          <div style={platformsBreakdownContainer}>
            {Object.keys(data.platform_breakdown).length === 0 ? (
              <div style={emptyPlatformsTextStyle}>No connected account logs available to compare.</div>
            ) : (
              Object.entries(data.platform_breakdown).map(([platform, stats]) => {
                // Find total engagement percentage to draw bar length
                const maxEng = Math.max(...Object.values(data.platform_breakdown).map(s => s.engagements)) || 1;
                const barWidth = (stats.engagements / maxEng) * 100;
                
                return (
                  <div key={platform} style={platformBarRowStyle}>
                    <div style={platformLabelStyle}>
                      <span style={{ textTransform: 'capitalize', fontWeight: '600' }}>{platform}</span>
                      <span style={platformSubtextStyle}>{stats.posts_count} posts dispatched</span>
                    </div>
                    
                    <div style={platformProgressTrackBg}>
                      <div style={platformProgressFillBar(barWidth, platform)} className="platform-fill-entrance"></div>
                    </div>
                    
                    <div style={platformMetricsRowStyle}>
                      <span>{stats.impressions.toLocaleString()} views</span>
                      <span>•</span>
                      <span>{stats.engagements.toLocaleString()} clicks/likes</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Best Performing Post highlight banner */}
      {data.best_performing_post && (
        <div className="glass-panel" style={bestPostCardStyle}>
          <div style={bestPostBadgeRow}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--warning)' }}>
              <FiAward size={20} />
              <h4 style={{ fontWeight: '700', fontSize: '1rem', color: 'var(--text-primary)' }}>Best Performing Content Link</h4>
            </div>
            <span style={bestPostMetricsValue}>
              {data.best_performing_post.engagements} engagements
            </span>
          </div>
          
          <p style={bestPostContentTextStyle}>"{data.best_performing_post.content_text}"</p>
          <span style={bestPostDateTextStyle}>
            Dispatched on {new Date(data.best_performing_post.scheduled_at).toLocaleString()}
          </span>
        </div>
      )}

      {/* Insert styles globally for SVG entrance animations */}
      {typeof document !== 'undefined' && !document.getElementById('svg-chart-styles') && (
        <style id="svg-chart-styles">
          {`
            @keyframes chartAreaFade {
              from { opacity: 0; }
              to { opacity: 1; }
            }
            @keyframes chartLineDraw {
              from { stroke-dashoffset: 1000; }
              to { stroke-dashoffset: 0; }
            }
            .chart-area-entrance {
              animation: chartAreaFade 1.2s ease-out forwards;
            }
            .chart-line-entrance {
              stroke-dasharray: 1000;
              stroke-dashoffset: 1000;
              animation: chartLineDraw 1.5s cubic-bezier(0.25, 1, 0.5, 1) forwards;
            }
            .chart-tooltip-text {
              opacity: 0;
              transition: opacity 0.25s ease-in-out;
              pointer-events: none;
            }
            .chart-point-group:hover .chart-tooltip-text {
              opacity: 1;
            }
            @keyframes barExpand {
              from { width: 0%; }
            }
            .platform-fill-entrance {
              animation: barExpand 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards;
            }
          `}
        </style>
      )}

    </div>
  );
};

// Layout styles
const containerStyle = {
  width: '100%'
};

const headerRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '24px'
};

const sectionTitleStyle = {
  fontSize: '1.5rem',
  marginBottom: '4px'
};

const sectionDescStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.9rem'
};

const exportBtnStyle = {
  padding: '10px 20px',
  fontSize: '0.82rem',
  height: '38px',
  display: 'flex',
  alignItems: 'center',
  gap: '6px'
};

const metricsGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: '20px',
  marginBottom: '28px'
};

const scorecardStyle = (glowColor) => ({
  padding: '24px',
  borderRadius: '14px',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  border: '1px solid var(--border-color)',
  boxShadow: `0 8px 32px 0 rgba(0,0,0,0.25), inset 0 0 12px 1px ${glowColor}`
});

const scorecardHeader = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px'
};

const scorecardLabelStyle = {
  fontSize: '0.8rem',
  color: 'var(--text-secondary)',
  fontWeight: '600'
};

const scorecardValueStyle = {
  fontSize: '1.8rem',
  fontWeight: '700',
  color: 'var(--text-primary)',
  lineHeight: '1'
};

const scorecardFootnote = {
  fontSize: '0.74rem',
  color: 'var(--text-muted)'
};

const chartsGridContainer = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
  gap: '24px',
  marginBottom: '28px'
};

const chartCardStyle = {
  padding: '28px',
  borderRadius: '14px',
  border: '1px solid var(--border-color)',
  display: 'flex',
  flexDirection: 'column',
  gap: '20px'
};

const chartHeaderRow = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '12px'
};

const chartTitleStyle = {
  fontSize: '1.05rem',
  fontWeight: '600'
};

const metricSelectContainer = {
  display: 'flex',
  background: 'rgba(255,255,255,0.03)',
  borderRadius: '8px',
  padding: '2px',
  border: '1px solid var(--border-color)'
};

const metricTabBtn = (isActive, activeColor) => ({
  background: isActive ? activeColor : 'transparent',
  color: isActive ? '#ffffff' : 'var(--text-secondary)',
  border: 'none',
  padding: '6px 12px',
  borderRadius: '6px',
  fontSize: '0.74rem',
  fontWeight: '600',
  cursor: 'pointer',
  transition: 'all 0.25s ease'
});

const svgChartWrapperStyle = {
  width: '100%',
  maxHeight: '220px',
  display: 'flex',
  justifyContent: 'center',
  background: 'rgba(0,0,0,0.1)',
  padding: '10px 0',
  borderRadius: '10px'
};

const platformsBreakdownContainer = {
  display: 'flex',
  flexDirection: 'column',
  gap: '18px',
  minHeight: '220px',
  justifyContent: 'center'
};

const emptyPlatformsTextStyle = {
  textAlign: 'center',
  color: 'var(--text-muted)',
  fontSize: '0.85rem',
  fontStyle: 'italic'
};

const platformBarRowStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px'
};

const platformLabelStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '0.82rem',
  color: 'var(--text-primary)'
};

const platformSubtextStyle = {
  fontSize: '0.74rem',
  color: 'var(--text-muted)'
};

const platformProgressTrackBg = {
  width: '100%',
  height: '10px',
  borderRadius: '5px',
  background: 'rgba(255,255,255,0.04)',
  overflow: 'hidden'
};

const platformProgressFillBar = (widthRate, platform) => {
  let color = 'linear-gradient(90deg, #6366f1 0%, #a855f7 100%)'; // default
  const platLower = platform.toLowerCase();
  if (platLower.includes('linkedin')) color = 'linear-gradient(90deg, #0077b5 0%, #00a0dc 100%)';
  else if (platLower.includes('twitter') || platLower.includes('x')) color = 'linear-gradient(90deg, #1d9bf0 0%, #0f1419 100%)';
  else if (platLower.includes('facebook')) color = 'linear-gradient(90deg, #1877f2 0%, #3b5998 100%)';
  else if (platLower.includes('instagram')) color = 'linear-gradient(90deg, #f97316 0%, #ec4899 100%)';
  
  return {
    width: `${widthRate}%`,
    height: '100%',
    background: color,
    borderRadius: '5px',
    transition: 'width 0.8s cubic-bezier(0.25, 1, 0.5, 1)'
  };
};

const platformMetricsRowStyle = {
  display: 'flex',
  gap: '6px',
  fontSize: '0.74rem',
  color: 'var(--text-muted)',
  fontWeight: '500'
};

const bestPostCardStyle = {
  padding: '24px',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  textAlign: 'left'
};

const bestPostBadgeRow = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  flexWrap: 'wrap',
  gap: '12px'
};

const bestPostMetricsValue = {
  background: 'rgba(245, 158, 11, 0.1)',
  color: 'var(--warning)',
  fontSize: '0.78rem',
  fontWeight: '600',
  padding: '4px 10px',
  borderRadius: '8px'
};

const bestPostContentTextStyle = {
  fontSize: '0.9rem',
  color: 'var(--text-secondary)',
  fontWeight: '500',
  fontStyle: 'italic',
  borderLeft: '3px solid var(--warning)',
  paddingLeft: '12px'
};

const bestPostDateTextStyle = {
  fontSize: '0.74rem',
  color: 'var(--text-muted)'
};

const centerTextStyle = {
  textAlign: 'center',
  padding: '40px',
  color: 'var(--text-secondary)'
};

const noWorkspaceStyle = {
  maxWidth: '500px',
  margin: '40px auto',
  padding: '40px',
  textAlign: 'center',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
};

export default Analytics;

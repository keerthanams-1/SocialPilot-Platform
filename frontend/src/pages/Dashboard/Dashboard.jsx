import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  FiLayout, FiUser, FiUsers, FiCalendar, 
  FiFolder, FiBarChart2, FiSettings, FiLogOut, FiMenu, FiLink,
  FiBell, FiCheckCircle, FiAlertCircle, FiInfo, FiLayers, FiEdit3, FiFileText, FiActivity
} from 'react-icons/fi';
import api from '../../services/api';
import Profile from '../Profile/Profile';
import TeamManagement from '../Team/TeamManagement';
import SocialAccounts from '../SocialAccounts/SocialAccounts';
import Scheduler from '../Scheduler/Scheduler';
import Campaigns from '../Campaigns/Campaigns';
import Analytics from '../Analytics/Analytics';
import Settings from '../Settings/Settings';
import Reports from '../Reports/Reports';
import Clients from '../Clients/Clients';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [schedulerSubTab, setSchedulerSubTab] = useState('compose');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useAuth();

  // Notifications drawer state
  const [notifications, setNotifications] = useState([]);
  const [showNotifDrawer, setShowNotifDrawer] = useState(false);

  const fetchNotifications = useCallback(async () => {
    const activeTeamId = localStorage.getItem('socialpilot_active_team_id');
    try {
      const url = activeTeamId ? `/notifications?team_id=${activeTeamId}` : '/notifications';
      const response = await api.get(url);
      const rawData = response.data;
      const notifArray = Array.isArray(rawData) ? rawData : (rawData?.data?.notifications || rawData?.data || []);
      setNotifications(Array.isArray(notifArray) ? notifArray : []);
    } catch (err) {
      console.error("Failed to fetch notifications", err);
      setNotifications([]);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 5000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Audit Logs state and fetch hook
  const [auditLogs, setAuditLogs] = useState([]);
  const [fetchingLogs, setFetchingLogs] = useState(false);

  const fetchAuditLogs = useCallback(async () => {
    const roleName = user?.role_name || user?.role?.name;
    if (roleName !== 'Administrator') return;
    setFetchingLogs(true);
    try {
      const response = await api.get('/auth/audit-logs');
      const rawData = response.data;
      const logsArray = Array.isArray(rawData) ? rawData : (rawData?.data?.logs || rawData?.data || []);
      setAuditLogs(Array.isArray(logsArray) ? logsArray : []);
    } catch (err) {
      console.error("Failed to fetch audit logs", err);
      setAuditLogs([]);
    } finally {
      setFetchingLogs(false);
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === 'audit-logs') {
      fetchAuditLogs();
    }
  }, [activeTab, fetchAuditLogs]);

  // Auto-initialize active team workspace if missing from local storage
  useEffect(() => {
    const resolveActiveTeam = async () => {
      const savedTeamId = localStorage.getItem('socialpilot_active_team_id');
      if (!savedTeamId) {
        try {
          const response = await api.get('/teams/my-teams');
          const rawData = response.data;
          const myTeams = Array.isArray(rawData) ? rawData : (rawData?.data?.teams || rawData?.data || []);
          if (Array.isArray(myTeams) && myTeams.length > 0) {
            localStorage.setItem('socialpilot_active_team_id', myTeams[0].id);
            fetchNotifications();
          }
        } catch (err) {
          console.error("Failed to resolve active workspace team", err);
        }
      }
    };
    resolveActiveTeam();
  }, [fetchNotifications]);

  const handleMarkAsRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      setNotifications(prev => Array.isArray(prev) ? prev.map(n => n.id === id ? { ...n, is_read: true } : n) : []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    const activeTeamId = localStorage.getItem('socialpilot_active_team_id');
    if (!activeTeamId) return;
    try {
      await api.post(`/notifications/read-all?team_id=${activeTeamId}`);
      setNotifications(prev => Array.isArray(prev) ? prev.map(n => ({ ...n, is_read: true })) : []);
    } catch (err) {
      console.error(err);
    }
  };

  const safeNotifs = Array.isArray(notifications) ? notifications : [];
  const unreadCount = safeNotifs.filter(n => !n.is_read).length;

  const handleLogout = async () => {
    await logout();
  };

  useEffect(() => {
    // Check if loaded inside an OAuth popup window
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    if (code) {
      if (window.opener) {
        window.opener.postMessage({
          type: 'oauth-success',
          platform: params.get('platform'),
          code: code,
          state: params.get('state'),
          team_id: params.get('team_id')
        }, '*');
        window.close();
      }
    }
  }, []);

  const [dashboardMetrics, setDashboardMetrics] = useState(null);

  const fetchDashboardMetrics = useCallback(async () => {
    const roleName = user?.role_name || user?.role?.name || 'Content Creator';
    let endpoint = '/dashboard/creator';
    if (roleName === 'Administrator') endpoint = '/dashboard/admin';
    else if (roleName === 'Business User') endpoint = '/dashboard/business';
    else if (roleName === 'Marketing Team' || roleName === 'Marketing Specialist') endpoint = '/dashboard/marketing';

    try {
      const response = await api.get(endpoint);
      setDashboardMetrics(response.data?.data || response.data);
    } catch (err) {
      console.error("Failed to fetch dashboard metrics", err);
    }
  }, [user]);

  useEffect(() => {
    fetchDashboardMetrics();
  }, [fetchDashboardMetrics]);

  const renderRoleDashboard = () => {
    const roleName = user?.role_name || user?.role?.name || 'Content Creator';

    if (roleName === 'Administrator') {
      return (
        <div style={welcomeCardStyle} className="glass-panel animate-fade-in">
          <h2 style={tabTitleStyle}>🛡️ Administrator Workspace Control</h2>
          <p style={tabDescStyle}>
            Welcome back, <strong>{user?.name || user?.full_name}</strong>! You have full administrative control over SocialPilot.
          </p>
          
          <div style={statsGridStyle}>
            <div style={statCardStyle} className="glass-panel">
              <h4>Registered Users</h4>
              <p style={statNumberStyle}>{dashboardMetrics?.total_users || 4}</p>
              <span>Total Active Accounts</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Active Campaigns</h4>
              <p style={statNumberStyle}>{dashboardMetrics?.active_campaigns || 3}</p>
              <span>Running Marketing Plans</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Worker & Cluster Status</h4>
              <p style={{ ...statNumberStyle, fontSize: '1.4rem', color: 'var(--success)', marginTop: '12px' }}>
                {dashboardMetrics?.worker_status?.celery_beat === 'running' ? '⚡ 100% Operational' : 'Active'}
              </p>
              <span>Redis: {dashboardMetrics?.redis_status?.status || 'connected'} • Postgres: {dashboardMetrics?.postgres_status?.status || 'connected'}</span>
            </div>
          </div>

          <div style={shortcutSectionStyle}>
            <h4 style={shortcutTitleStyle}>Quick Action Shortcuts</h4>
            <div style={shortcutGridStyle}>
              <button className="btn-primary" onClick={() => setActiveTab('team')} style={{ height: '36px', fontSize: '0.82rem' }}>Manage Collaborators</button>
              <button className="btn-secondary" onClick={() => setActiveTab('social')} style={{ height: '36px', fontSize: '0.82rem' }}>Add Social Target</button>
              <button className="btn-secondary" onClick={() => setActiveTab('scheduler')} style={{ height: '36px', fontSize: '0.82rem' }}>Content Scheduler</button>
              <button className="btn-secondary" onClick={() => setActiveTab('settings')} style={{ height: '36px', fontSize: '0.82rem' }}>Workspace Config</button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginTop: '24px' }}>
            <div className="glass-panel" style={{ padding: '20px', textAlign: 'left' }}>
              <h4 style={{ margin: '0 0 16px 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
                <FiActivity size={18} style={{ color: 'var(--primary)' }} /> Recent Workspace Activity
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--primary)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>🚀 Q3 Brand Campaign Launched</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Assigned to 3 channels • 2 hours ago</div>
                </div>
                <div style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--success)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>✅ LinkedIn Digest Published</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Dispatched successfully • 4 hours ago</div>
                </div>
                <div style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--warning)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>📅 4 Posts Scheduled for Next Week</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Visual Calendar queue synced • Yesterday</div>
                </div>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px', textAlign: 'left' }}>
              <h4 style={{ margin: '0 0 16px 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
                <FiFolder size={18} style={{ color: 'var(--success)' }} /> Active Campaign Progress
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
                    <span>Summer Product Launch</span>
                    <strong style={{ color: 'var(--text-primary)' }}>78% Completed</strong>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: '78%', height: '100%', background: 'linear-gradient(90deg, #6366f1, #8b5cf6)' }}></div>
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
                    <span>Brand Awareness Q3</span>
                    <strong style={{ color: 'var(--text-primary)' }}>45% Completed</strong>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: '45%', height: '100%', background: 'linear-gradient(90deg, #10b981, #059669)' }}></div>
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: '6px', color: 'var(--text-secondary)' }}>
                    <span>Customer Spotlight Series</span>
                    <strong style={{ color: 'var(--text-primary)' }}>92% Completed</strong>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: '92%', height: '100%', background: 'linear-gradient(90deg, #f59e0b, #ec4899)' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (roleName === 'Business User') {
      return (
        <div style={welcomeCardStyle} className="glass-panel animate-fade-in">
          <h2 style={tabTitleStyle}>📈 Business Strategy Console</h2>
          <p style={tabDescStyle}>
            Welcome back, <strong>{user?.name}</strong>! Track campaign budget allocations, objectives, and analytics.
          </p>
          
          <div style={statsGridStyle}>
            <div style={statCardStyle} className="glass-panel">
              <h4>Campaign Budget</h4>
              <p style={statNumberStyle}>$5,000</p>
              <span>Q3 Allocation Set</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Impressions</h4>
              <p style={statNumberStyle}>1,250</p>
              <span>Weekly Organic Reach</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Conversion Rate</h4>
              <p style={statNumberStyle}>6.8%</p>
              <span>Click-through rate</span>
            </div>
          </div>

          <div style={shortcutSectionStyle}>
            <h4 style={shortcutTitleStyle}>Quick Action Shortcuts</h4>
            <div style={shortcutGridStyle}>
              <button className="btn-primary" onClick={() => setActiveTab('campaigns')} style={{ height: '36px', fontSize: '0.82rem' }}>Create Campaign</button>
              <button className="btn-secondary" onClick={() => setActiveTab('analytics')} style={{ height: '36px', fontSize: '0.82rem' }}>Export Report CSV</button>
              <button className="btn-secondary" onClick={() => setActiveTab('team')} style={{ height: '36px', fontSize: '0.82rem' }}>View Team Status</button>
            </div>
          </div>
        </div>
      );
    }

    if (roleName === 'Marketing Team' || roleName === 'Marketing Specialist') {
      return (
        <div style={welcomeCardStyle} className="glass-panel animate-fade-in">
          <h2 style={tabTitleStyle}>📣 Marketing Specialist Command Center</h2>
          <p style={tabDescStyle}>
            Welcome back, <strong>{user?.name || user?.full_name}</strong>! Oversee multi-client marketing strategies, campaign dispatches, publishing calendars, and performance reports.
          </p>
          
          {/* Key Marketing KPI Cards */}
          <div style={statsGridStyle}>
            <div style={statCardStyle} className="glass-panel">
              <h4>Active Clients</h4>
              <p style={statNumberStyle}>4</p>
              <span>Corporate Accounts Managed</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Monthly Spend</h4>
              <p style={statNumberStyle}>$55,000</p>
              <span>Total Retainer Volume</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Active Campaigns</h4>
              <p style={statNumberStyle}>3</p>
              <span>Multi-Channel Plans</span>
            </div>
            <div style={statCardStyle} className="glass-panel">
              <h4>Avg. Campaign ROI</h4>
              <p style={{ ...statNumberStyle, color: 'var(--success)' }}>412.5%</p>
              <span>Across All Client Brands</span>
            </div>
          </div>

          {/* Client Portfolio Overview Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px', textAlign: 'left' }}>
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h4 style={{ margin: '0 0 14px 0', fontSize: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiUsers style={{ color: 'var(--primary)' }} /> Client Accounts Overview
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--primary)' }}>
                  <div>
                    <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>Acme Enterprise Tech</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Software & Cloud • 2 Campaigns</div>
                  </div>
                  <span style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--success)' }}>$15,000/mo</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--success)' }}>
                  <div>
                    <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>TechFlow SaaS Solutions</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Developer Tools • 3 Campaigns</div>
                  </div>
                  <span style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--success)' }}>$12,500/mo</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--warning)' }}>
                  <div>
                    <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>Nexus Health Systems</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>HealthTech • 1 Campaign</div>
                  </div>
                  <span style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--success)' }}>$18,000/mo</span>
                </div>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px' }}>
              <h4 style={{ margin: '0 0 14px 0', fontSize: '1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiBarChart2 style={{ color: 'var(--success)' }} /> Marketing Funnel Breakdown
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                    <span>Top of Funnel (Brand Reach)</span>
                    <strong>1,550,000 Reach</strong>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: '100%', height: '100%', background: 'linear-gradient(90deg, #6366f1, #8b5cf6)' }}></div>
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                    <span>Middle of Funnel (Engagement & Clicks)</span>
                    <strong>124,500 Engagements</strong>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: '65%', height: '100%', background: 'linear-gradient(90deg, #10b981, #059669)' }}></div>
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                    <span>Bottom of Funnel (Leads & Sales)</span>
                    <strong>8,920 Conversions</strong>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: '35%', height: '100%', background: 'linear-gradient(90deg, #f59e0b, #ec4899)' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Dedicated Marketing Shortcuts */}
          <div style={shortcutSectionStyle}>
            <h4 style={shortcutTitleStyle}>Marketing Specialist Navigation Modules</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', marginTop: '12px' }}>
              <button className="btn-primary" onClick={() => setActiveTab('overview')} style={{ height: '38px', fontSize: '0.8rem' }}>🏠 1. Dashboard</button>
              <button className="btn-secondary" onClick={() => setActiveTab('social')} style={{ height: '38px', fontSize: '0.8rem' }}>👥 2. Clients</button>
              <button className="btn-secondary" onClick={() => setActiveTab('campaigns')} style={{ height: '38px', fontSize: '0.8rem' }}>🎯 3. Campaign Mgmt</button>
              <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); }} style={{ height: '38px', fontSize: '0.8rem' }}>✍️ 4. Content Scheduling</button>
              <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('calendar'); }} style={{ height: '38px', fontSize: '0.8rem' }}>📅 5. Publishing Calendar</button>
              <button className="btn-secondary" onClick={() => setActiveTab('analytics')} style={{ height: '38px', fontSize: '0.8rem' }}>📊 6. Analytics</button>
              <button className="btn-secondary" onClick={() => setActiveTab('reports')} style={{ height: '38px', fontSize: '0.8rem' }}>📑 7. Reports</button>
              <button className="btn-secondary" onClick={() => setActiveTab('notifications')} style={{ height: '38px', fontSize: '0.8rem' }}>🔔 8. Notifications</button>
              <button className="btn-secondary" onClick={() => setActiveTab('profile')} style={{ height: '38px', fontSize: '0.8rem' }}>👤 9. Profile</button>
              <button className="btn-secondary" onClick={() => setActiveTab('settings')} style={{ height: '38px', fontSize: '0.8rem' }}>⚙️ 10. Settings</button>
              <button className="btn-secondary" onClick={logout} style={{ height: '38px', fontSize: '0.8rem', color: 'var(--error)' }}>🚪 11. Logout</button>
            </div>
          </div>
        </div>
      );
    }

    // Default: Content Creator Dashboard
    return (
      <div style={welcomeCardStyle} className="glass-panel animate-fade-in">
        <h2 style={tabTitleStyle}>✍️ Content Creator Studio</h2>
        <p style={tabDescStyle}>
          Welcome back, <strong>{user?.name || user?.full_name}</strong>! Compose drafts, upload media, set scheduling times, check device previews, and manage your queues.
        </p>
        
        <div style={statsGridStyle}>
          <div style={statCardStyle} className="glass-panel">
            <h4>My Drafts</h4>
            <p style={statNumberStyle}>4</p>
            <span>Awaiting Workspace Review</span>
          </div>
          <div style={statCardStyle} className="glass-panel">
            <h4>Assigned Campaigns</h4>
            <p style={statNumberStyle}>3</p>
            <span>Q3 Enterprise & Summer Boost</span>
          </div>
          <div style={statCardStyle} className="glass-panel">
            <h4>Target Platforms</h4>
            <p style={statNumberStyle}>5</p>
            <span>Facebook, IG, LinkedIn, X, YouTube</span>
          </div>
        </div>

        <div style={shortcutSectionStyle}>
          <h4 style={shortcutTitleStyle}>Content Creator Workflow Tools</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginTop: '12px' }}>
            <button className="btn-primary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              ✍️ Create New Post
            </button>
            <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              🖼️ Upload Media Asset
            </button>
            <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              📱 Select Channels & Caption
            </button>
            <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              ⏰ Schedule Date & Time
            </button>
            <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              👁️ Device Post Preview
            </button>
            <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('calendar'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              📅 Publishing Calendar
            </button>
            <button className="btn-secondary" onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('queue'); }} style={{ height: '40px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
              📋 Queue Management
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return <Profile />;
      case 'team':
        return <TeamManagement />;
      case 'clients':
        return <Clients />;
      case 'social':
        return (user?.role_name || user?.role?.name) === 'Marketing Team' ? <Clients /> : <SocialAccounts />;
      case 'scheduler':
        return <Scheduler initialTab={schedulerSubTab} />;
      case 'campaigns':
        return <Campaigns />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return <Settings />;
      case 'reports':
        return <Reports />;
      case 'notifications':
        return (
          <div style={containerStyle}>
            <div style={notifPageHeader}>
              <div>
                <h2 style={tabTitleStyle}>Workspace Notifications Log</h2>
                <p style={tabDescStyle}>Stay updated with automated dispatch statuses and workspace security logs.</p>
              </div>
              {safeNotifs.some(n => !n.is_read) && (
                <button className="btn-secondary" onClick={handleMarkAllRead} style={{ height: '38px', fontSize: '0.8rem' }}>
                  Mark All as Read
                </button>
              )}
            </div>

            {safeNotifs.length === 0 ? (
              <div className="glass-panel animate-fade-in" style={emptyStateStyle}>
                <FiBell size={40} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
                <h3>No Alerts Found</h3>
                <p>You are fully up to date! Logs will appear here as postings succeed or fail.</p>
              </div>
            ) : (
              <div style={notifListStyle}>
                {safeNotifs.map(n => (
                  <div 
                    key={n.id} 
                    className="glass-panel" 
                    style={notifItemCardStyle(n.is_read, n.type)}
                  >
                    <div style={{ display: 'flex', gap: '14px', alignItems: 'start' }}>
                      <div style={notifIconContainerStyle(n.type)}>
                        {n.type === 'error' ? <FiAlertCircle size={18} /> : n.type === 'success' ? <FiCheckCircle size={18} /> : <FiInfo size={18} />}
                      </div>
                      <div style={{ textAlign: 'left' }}>
                        <strong style={notifCardTitleStyle(n.is_read)}>{n.title}</strong>
                        <p style={notifCardDescStyle}>{n.message}</p>
                        <span style={notifCardTimeStyle}>{new Date(n.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    {!n.is_read && (
                      <button 
                        className="btn-primary" 
                        onClick={() => handleMarkAsRead(n.id)}
                        style={notifCardReadBtn}
                      >
                        Mark Read
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case 'audit-logs':
        return (
          <div style={containerStyle}>
            <div style={notifPageHeader}>
              <div>
                <h2 style={tabTitleStyle}>System Audit & Activity Logs</h2>
                <p style={tabDescStyle}>Track every workspace security event, authentication trigger, and session lifespan status.</p>
              </div>
              <button 
                className="btn-secondary" 
                onClick={fetchAuditLogs} 
                disabled={fetchingLogs}
                style={{ height: '38px', fontSize: '0.8rem' }}
              >
                {fetchingLogs ? 'Refreshing...' : 'Refresh Logs'}
              </button>
            </div>

            <div className="glass-panel animate-fade-in" style={{ padding: '24px', overflowX: 'auto', border: '1px solid var(--border-color)' }}>
              {(!Array.isArray(auditLogs) || auditLogs.length === 0) ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  <FiActivity size={32} style={{ marginBottom: '12px' }} />
                  <h4>No Security Logs Recorded</h4>
                  <p>Authentications and session changes will appear here in real time.</p>
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-secondary)', fontWeight: '600' }}>
                      <th style={{ padding: '12px' }}>Timestamp</th>
                      <th style={{ padding: '12px' }}>User</th>
                      <th style={{ padding: '12px' }}>Email</th>
                      <th style={{ padding: '12px' }}>Role</th>
                      <th style={{ padding: '12px' }}>Action</th>
                      <th style={{ padding: '12px' }}>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(Array.isArray(auditLogs) ? auditLogs : []).map((log) => (
                      <tr 
                        key={log.id} 
                        style={{ 
                          borderBottom: '1px solid var(--border-color)',
                          transition: 'background 0.2s',
                          color: 'var(--text-primary)'
                        }}
                        className="table-row-hover"
                      >
                        <td style={{ padding: '12px', whiteSpace: 'nowrap' }}>
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', fontWeight: '500' }}>{log.user_name}</td>
                        <td style={{ padding: '12px' }}>{log.user_email}</td>
                        <td style={{ padding: '12px' }}>
                          <span style={roleBadgeStyle(log.role_name)}>
                            {log.role_name}
                          </span>
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={actionBadgeStyle(log.action)}>
                            {log.action}
                          </span>
                        </td>
                        <td style={{ padding: '12px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                          {log.ip_address || '127.0.0.1'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        );
      default:
        return renderRoleDashboard();
    }
  };

  return (
    <div style={layoutStyle}>
      {/* Sidebar Navigation */}
      <div style={sidebarOpen ? sidebarStyle : sidebarClosedStyle} className="glass-panel">
        <div style={logoContainerStyle}>
          <h2 style={logoTextStyle}>SocialPilot</h2>
        </div>

        <div style={navGroupStyle}>
          {(user?.role_name || user?.role?.name) === 'Content Creator' ? (
            <>
              <button 
                style={activeTab === 'overview' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('overview'); setShowNotifDrawer(false); }}
              >
                <FiLayout size={18} />
                {sidebarOpen && <span>Dashboard</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' && schedulerSubTab === 'queue' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('queue'); setShowNotifDrawer(false); }}
              >
                <FiLayers size={18} />
                {sidebarOpen && <span>My Posts</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' && schedulerSubTab === 'compose' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); setShowNotifDrawer(false); }}
              >
                <FiEdit3 size={18} />
                {sidebarOpen && <span>Content Scheduling</span>}
              </button>
              <button 
                style={activeTab === 'campaigns' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('campaigns'); setShowNotifDrawer(false); }}
              >
                <FiFolder size={18} />
                {sidebarOpen && <span>Campaigns</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' && schedulerSubTab === 'calendar' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('calendar'); setShowNotifDrawer(false); }}
              >
                <FiCalendar size={18} />
                {sidebarOpen && <span>My Calendar</span>}
              </button>
              <button 
                style={activeTab === 'notifications' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('notifications'); setShowNotifDrawer(false); }}
              >
                <FiBell size={18} />
                {sidebarOpen && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Notifications 
                    {safeNotifs.filter(n => !n.is_read).length > 0 && (
                      <span style={{ background: 'var(--error)', color: '#fff', fontSize: '0.66rem', padding: '1px 5px', borderRadius: '8px', fontWeight: 'bold' }}>
                        {safeNotifs.filter(n => !n.is_read).length}
                      </span>
                    )}
                  </span>
                )}
              </button>
              <button 
                style={activeTab === 'profile' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('profile'); setShowNotifDrawer(false); }}
              >
                <FiUser size={18} />
                {sidebarOpen && <span>Profile</span>}
              </button>
              <button 
                style={activeTab === 'settings' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('settings'); setShowNotifDrawer(false); }}
              >
                <FiSettings size={18} />
                {sidebarOpen && <span>Settings</span>}
              </button>
            </>
          ) : (user?.role_name || user?.role?.name) === 'Marketing Team' || (user?.role_name || user?.role?.name) === 'Marketing Specialist' ? (
            <>
              <button 
                style={activeTab === 'overview' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('overview'); setShowNotifDrawer(false); }}
              >
                <FiLayout size={18} />
                {sidebarOpen && <span>Dashboard</span>}
              </button>
              <button 
                style={activeTab === 'social' || activeTab === 'team' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('social'); setShowNotifDrawer(false); }}
              >
                <FiUsers size={18} />
                {sidebarOpen && <span>Clients</span>}
              </button>
              <button 
                style={activeTab === 'campaigns' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('campaigns'); setShowNotifDrawer(false); }}
              >
                <FiFolder size={18} />
                {sidebarOpen && <span>Campaign Management</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' && schedulerSubTab === 'compose' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); setShowNotifDrawer(false); }}
              >
                <FiEdit3 size={18} />
                {sidebarOpen && <span>Content Scheduling</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' && schedulerSubTab === 'calendar' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('calendar'); setShowNotifDrawer(false); }}
              >
                <FiCalendar size={18} />
                {sidebarOpen && <span>Publishing Calendar</span>}
              </button>
              <button 
                style={activeTab === 'analytics' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('analytics'); setShowNotifDrawer(false); }}
              >
                <FiBarChart2 size={18} />
                {sidebarOpen && <span>Analytics</span>}
              </button>
              <button 
                style={activeTab === 'reports' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('reports'); setShowNotifDrawer(false); }}
              >
                <FiFileText size={18} />
                {sidebarOpen && <span>Reports</span>}
              </button>
              <button 
                style={activeTab === 'notifications' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('notifications'); setShowNotifDrawer(false); }}
              >
                <FiBell size={18} />
                {sidebarOpen && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Notifications 
                    {safeNotifs.filter(n => !n.is_read).length > 0 && (
                      <span style={{ background: 'var(--error)', color: '#fff', fontSize: '0.66rem', padding: '1px 5px', borderRadius: '8px', fontWeight: 'bold' }}>
                        {safeNotifs.filter(n => !n.is_read).length}
                      </span>
                    )}
                  </span>
                )}
              </button>
              <button 
                style={activeTab === 'profile' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('profile'); setShowNotifDrawer(false); }}
              >
                <FiUser size={18} />
                {sidebarOpen && <span>Profile</span>}
              </button>
              <button 
                style={activeTab === 'settings' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('settings'); setShowNotifDrawer(false); }}
              >
                <FiSettings size={18} />
                {sidebarOpen && <span>Settings</span>}
              </button>
              <button 
                style={{ ...navItemStyle, color: 'var(--error)', marginTop: '8px' }} 
                onClick={logout}
              >
                <FiLogOut size={18} />
                {sidebarOpen && <span>Logout</span>}
              </button>
            </>
          ) : (user?.role_name || user?.role?.name) === 'Administrator' ? (
            <>
              <button 
                style={activeTab === 'overview' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('overview'); setShowNotifDrawer(false); }}
              >
                <FiLayout size={18} />
                {sidebarOpen && <span>Dashboard</span>}
              </button>
              <button 
                style={activeTab === 'team' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('team'); setShowNotifDrawer(false); }}
              >
                <FiUsers size={18} />
                {sidebarOpen && <span>Workspace Users</span>}
              </button>
              <button 
                style={activeTab === 'social' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('social'); setShowNotifDrawer(false); }}
              >
                <FiLink size={18} />
                {sidebarOpen && <span>Social Channels</span>}
              </button>
              <button 
                style={activeTab === 'campaigns' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('campaigns'); setShowNotifDrawer(false); }}
              >
                <FiFolder size={18} />
                {sidebarOpen && <span>Campaigns</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' && schedulerSubTab === 'compose' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); setShowNotifDrawer(false); }}
              >
                <FiEdit3 size={18} />
                {sidebarOpen && <span>Scheduler</span>}
              </button>
              <button 
                style={activeTab === 'analytics' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('analytics'); setShowNotifDrawer(false); }}
              >
                <FiBarChart2 size={18} />
                {sidebarOpen && <span>Analytics</span>}
              </button>
              <button 
                style={activeTab === 'reports' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('reports'); setShowNotifDrawer(false); }}
              >
                <FiFileText size={18} />
                {sidebarOpen && <span>Reports</span>}
              </button>
              <button 
                style={activeTab === 'audit-logs' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('audit-logs'); setShowNotifDrawer(false); }}
              >
                <FiActivity size={18} />
                {sidebarOpen && <span>Audit & Activity Logs</span>}
              </button>
              <button 
                style={activeTab === 'notifications' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('notifications'); setShowNotifDrawer(false); }}
              >
                <FiBell size={18} />
                {sidebarOpen && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Notifications 
                    {safeNotifs.filter(n => !n.is_read).length > 0 && (
                      <span style={{ background: 'var(--error)', color: '#fff', fontSize: '0.66rem', padding: '1px 5px', borderRadius: '8px', fontWeight: 'bold' }}>
                        {safeNotifs.filter(n => !n.is_read).length}
                      </span>
                    )}
                  </span>
                )}
              </button>
              <button 
                style={activeTab === 'profile' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('profile'); setShowNotifDrawer(false); }}
              >
                <FiUser size={18} />
                {sidebarOpen && <span>Profile</span>}
              </button>
              <button 
                style={activeTab === 'settings' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('settings'); setShowNotifDrawer(false); }}
              >
                <FiSettings size={18} />
                {sidebarOpen && <span>Settings</span>}
              </button>
            </>
          ) : (
            <>
              <button 
                style={activeTab === 'overview' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('overview'); setShowNotifDrawer(false); }}
              >
                <FiLayout size={18} />
                {sidebarOpen && <span>Overview</span>}
              </button>
              <button 
                style={activeTab === 'profile' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('profile'); setShowNotifDrawer(false); }}
              >
                <FiUser size={18} />
                {sidebarOpen && <span>My Profile</span>}
              </button>
              <button 
                style={activeTab === 'team' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('team'); setShowNotifDrawer(false); }}
              >
                <FiUsers size={18} />
                {sidebarOpen && <span>Team Workspace</span>}
              </button>
              <button 
                style={activeTab === 'social' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('social'); setShowNotifDrawer(false); }}
              >
                <FiLink size={18} />
                {sidebarOpen && <span>Social Channels</span>}
              </button>
              <button 
                style={activeTab === 'scheduler' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('scheduler'); setSchedulerSubTab('compose'); setShowNotifDrawer(false); }}
              >
                <FiCalendar size={18} />
                {sidebarOpen && <span>Scheduler</span>}
              </button>
              <button 
                style={activeTab === 'campaigns' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('campaigns'); setShowNotifDrawer(false); }}
              >
                <FiFolder size={18} />
                {sidebarOpen && <span>Campaigns</span>}
              </button>
              <button 
                style={activeTab === 'analytics' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('analytics'); setShowNotifDrawer(false); }}
              >
                <FiBarChart2 size={18} />
                {sidebarOpen && <span>Analytics</span>}
              </button>
              <button 
                style={activeTab === 'settings' ? activeNavItemStyle : navItemStyle} 
                onClick={() => { setActiveTab('settings'); setShowNotifDrawer(false); }}
              >
                <FiSettings size={18} />
                {sidebarOpen && <span>Settings</span>}
              </button>
            </>
          )}
        </div>

        <div style={sidebarFooterStyle}>
          {sidebarOpen && (
            <div style={userInfoStyle}>
              <span style={userNameStyle}>{user?.name || user?.full_name}</span>
              <span style={userRoleStyle}>{user?.role_name || user?.role?.name || 'Member'}</span>
            </div>
          )}
          <button style={logoutButtonStyle} onClick={handleLogout} title="Log Out">
            <FiLogOut size={18} />
            {sidebarOpen && <span>Log Out</span>}
          </button>
        </div>
      </div>

      {/* Main Dashboard Space */}
      <div style={mainContentStyle}>
        <header style={headerStyle} className="glass-panel">
          <button style={toggleSidebarBtnStyle} onClick={() => setSidebarOpen(!sidebarOpen)}>
            <FiMenu size={20} />
          </button>
          
          <div style={headerRightStyle}>
            {/* Notifications Bell Hub */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <button 
                type="button"
                style={notifBellBtnStyle} 
                onClick={() => setShowNotifDrawer(prev => !prev)}
                title="Notifications Hub"
              >
                <FiBell size={18} style={{ color: 'var(--primary)' }} />
                {unreadCount > 0 && (
                  <span style={notifBadgeStyle}>{unreadCount}</span>
                )}
              </button>

              {/* Notifications Floating Drawer Dropdown */}
              {showNotifDrawer && (
                <div style={notifDropdownStyle} className="glass-panel animate-fade-in">
                  <div style={notifHeaderStyle}>
                    <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-primary)' }}>Notifications</h4>
                    {unreadCount > 0 && (
                      <button 
                        type="button" 
                        onClick={handleMarkAllRead} 
                        style={notifMarkAllBtnStyle}
                      >
                        Mark all read
                      </button>
                    )}
                  </div>
                  
                  <div style={notifListContainerStyle}>
                    {notifications.length === 0 ? (
                      <div style={notifEmptyStyle}>All caught up! No notifications.</div>
                    ) : (
                      notifications.map(n => (
                        <div 
                          key={n.id} 
                          style={n.is_read ? notifRowReadStyle : notifRowUnreadStyle}
                          onClick={() => !n.is_read && handleMarkAsRead(n.id)}
                        >
                          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                            <div style={{ marginTop: '2px', display: 'flex' }}>
                              {n.type === 'success' ? (
                                <FiCheckCircle style={{ color: 'var(--success)', minWidth: '16px' }} />
                              ) : n.type === 'error' ? (
                                <FiAlertCircle style={{ color: 'var(--error)', minWidth: '16px' }} />
                              ) : (
                                <FiInfo style={{ color: 'var(--primary)', minWidth: '16px' }} />
                              )}
                            </div>
                            <div style={{ flex: 1, textAlign: 'left' }}>
                              <div style={notifTitleStyle}>{n.title}</div>
                              <div style={notifMessageStyle}>{n.message}</div>
                              <div style={notifTimeStyle}>{new Date(n.created_at).toLocaleString()}</div>
                            </div>
                            {!n.is_read && <span style={notifDotStyle}></span>}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <span style={userStatusIndicator}>● Active Session</span>
          </div>
        </header>
        <main style={contentZoneStyle}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

// Layout Positioning Style mappings
const layoutStyle = {
  display: 'flex',
  minHeight: '100vh',
  background: 'transparent',
};

const sidebarStyle = {
  width: 'var(--sidebar-width)',
  display: 'flex',
  flexDirection: 'column',
  borderRadius: '0px 24px 24px 0px',
  borderLeft: 'none',
  padding: '24px 16px',
  transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  zIndex: 10,
};

const sidebarClosedStyle = {
  ...sidebarStyle,
  width: '80px',
  alignItems: 'center',
};

const logoContainerStyle = {
  marginBottom: '40px',
  paddingLeft: '12px',
};

const logoTextStyle = {
  fontSize: '1.5rem',
  background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
};

const navGroupStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  flex: 1,
};

const navItemStyle = {
  background: 'none',
  border: 'none',
  borderRadius: '10px',
  color: 'var(--text-secondary)',
  padding: '12px 16px',
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  cursor: 'pointer',
  fontSize: '0.95rem',
  textAlign: 'left',
  width: '100%',
  transition: 'all 0.2s ease',
};

const activeNavItemStyle = {
  ...navItemStyle,
  background: 'rgba(99, 102, 241, 0.1)',
  color: 'var(--text-primary)',
  borderLeft: '3px solid var(--primary)',
  borderTopLeftRadius: '0px',
  borderBottomLeftRadius: '0px',
};

const disabledNavItemStyle = {
  ...navItemStyle,
  opacity: 0.3,
  cursor: 'not-allowed',
};

const sidebarFooterStyle = {
  borderTop: '1px solid var(--border-color)',
  paddingTop: '20px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
};

const userInfoStyle = {
  display: 'flex',
  flexDirection: 'column',
  paddingLeft: '12px',
};

const userNameStyle = {
  fontSize: '0.95rem',
  fontWeight: '600',
  color: 'var(--text-primary)',
};

const userRoleStyle = {
  fontSize: '0.8rem',
  color: 'var(--text-muted)',
};

const logoutButtonStyle = {
  ...navItemStyle,
  color: 'var(--error)',
  background: 'rgba(244, 63, 94, 0.05)',
};

const mainContentStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  padding: '24px',
  overflowY: 'auto',
  maxHeight: '100vh',
};

const headerStyle = {
  height: 'var(--header-height)',
  borderRadius: '16px',
  padding: '0px 24px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  marginBottom: '24px',
  position: 'relative',
  zIndex: 100,
};

const toggleSidebarBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-primary)',
  cursor: 'pointer',
};

const headerRightStyle = {
  display: 'flex',
  alignItems: 'center',
};

const userStatusIndicator = {
  fontSize: '0.8rem',
  color: 'var(--success)',
  fontWeight: '500',
};

const contentZoneStyle = {
  flex: 1,
};

const containerStyle = {
  width: '100%'
};

const emptyStateStyle = {
  padding: '64px 32px',
  textAlign: 'center',
  color: 'var(--text-muted)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
};

const welcomeCardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
};

const tabTitleStyle = {
  fontSize: '1.5rem',
  marginBottom: '8px',
};

const tabDescStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.95rem',
  marginBottom: '32px',
};

const statsGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
  gap: '20px',
};

const statCardStyle = {
  padding: '24px',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

const statNumberStyle = {
  fontSize: '2.5rem',
  fontWeight: '800',
  color: 'var(--primary)',
};

const shortcutSectionStyle = {
  marginTop: '28px',
  borderTop: '1px solid var(--border-color)',
  paddingTop: '20px',
  textAlign: 'left'
};

const shortcutTitleStyle = {
  fontSize: '0.98rem',
  fontWeight: '600',
  color: 'var(--text-secondary)',
  marginBottom: '12px'
};

const shortcutGridStyle = {
  display: 'flex',
  gap: '12px',
  flexWrap: 'wrap'
};

const alertsContainerStyle = {
  marginTop: '20px',
  background: 'rgba(244, 63, 94, 0.04)',
  border: '1px solid rgba(244, 63, 94, 0.15)',
  padding: '16px',
  borderRadius: '10px',
  textAlign: 'left'
};

const alertItemStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  fontSize: '0.84rem',
  color: 'var(--text-secondary)',
  gap: '16px'
};

const alertBtnStyle = {
  padding: '6px 12px',
  fontSize: '0.78rem',
  height: '30px'
};

const notifBellBtnStyle = {
  background: 'rgba(255, 255, 255, 0.45)', // opaque frosted circle
  border: '1px solid var(--border-color)',
  borderRadius: '50%',
  width: '36px',
  height: '36px',
  color: 'var(--primary)', // indigo color for maximum visibility
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  position: 'relative',
  outline: 'none',
};

const notifBadgeStyle = {
  position: 'absolute',
  top: '-1px',
  right: '-1px',
  background: 'var(--error)',
  color: '#ffffff',
  fontSize: '0.62rem',
  fontWeight: '700',
  borderRadius: '10px',
  padding: '1px 4px',
  border: '2px solid var(--bg-dark)',
};

const notifDropdownStyle = {
  position: 'absolute',
  top: '46px',
  right: '0',
  width: '320px',
  maxHeight: '380px',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
  boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
  display: 'flex',
  flexDirection: 'column',
  zIndex: 9999,
  overflow: 'hidden',
  background: '#ffffff',
};

const notifHeaderStyle = {
  padding: '12px 16px',
  borderBottom: '1px solid var(--border-color)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

const notifMarkAllBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--primary)',
  fontSize: '0.78rem',
  fontWeight: '600',
  cursor: 'pointer',
  padding: '0',
  outline: 'none'
};

const notifListContainerStyle = {
  overflowY: 'auto',
  flex: 1,
};

const notifRowStyle = {
  padding: '12px 16px',
  borderBottom: '1px solid var(--border-color)',
  transition: 'background-color 0.2s ease',
  cursor: 'pointer',
};

const notifRowUnreadStyle = {
  ...notifRowStyle,
  backgroundColor: 'rgba(99,102,241,0.03)',
};

const notifRowReadStyle = {
  ...notifRowStyle,
  opacity: 0.6,
};

const notifTitleStyle = {
  fontSize: '0.8rem',
  fontWeight: '600',
  color: 'var(--text-primary)',
  marginBottom: '2px',
};

const notifMessageStyle = {
  fontSize: '0.76rem',
  color: 'var(--text-secondary)',
  lineHeight: '1.4',
  marginBottom: '4px',
};

const notifTimeStyle = {
  fontSize: '0.66rem',
  color: 'var(--text-muted)',
};

const notifDotStyle = {
  width: '6px',
  height: '6px',
  borderRadius: '50%',
  backgroundColor: 'var(--primary)',
  alignSelf: 'center',
};

const notifEmptyStyle = {
  padding: '32px 16px',
  textAlign: 'center',
  color: 'var(--text-muted)',
  fontSize: '0.8rem',
  fontStyle: 'italic',
};

const notifPageHeader = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '20px',
  flexWrap: 'wrap',
  gap: '12px'
};

const notifListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  width: '100%',
  maxWidth: '800px'
};

const notifItemCardStyle = (isRead, type) => {
  let border = '1px solid var(--border-color)';
  let bg = 'rgba(255, 255, 255, 0.01)';
  if (!isRead) {
    if (type === 'error') {
      border = '1px solid rgba(244, 63, 94, 0.2)';
      bg = 'rgba(244, 63, 94, 0.02)';
    } else if (type === 'success') {
      border = '1px solid rgba(16, 185, 129, 0.2)';
      bg = 'rgba(16, 185, 129, 0.02)';
    } else {
      border = '1px solid rgba(99, 102, 241, 0.2)';
      bg = 'rgba(99, 102, 241, 0.02)';
    }
  }
  return {
    padding: '16px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderRadius: '10px',
    border: border,
    background: bg,
    gap: '16px'
  };
};

const notifIconContainerStyle = (type) => {
  let color = 'var(--text-secondary)';
  if (type === 'error') color = 'var(--error)';
  else if (type === 'success') color = 'var(--success)';
  else if (type === 'info') color = 'var(--primary)';
  return {
    color: color,
    display: 'flex',
    alignItems: 'center',
    marginTop: '2px'
  };
};

const notifCardTitleStyle = (isRead) => ({
  fontSize: '0.94rem',
  fontWeight: isRead ? '500' : '600',
  color: isRead ? 'var(--text-secondary)' : 'var(--text-primary)'
});

const notifCardDescStyle = {
  fontSize: '0.84rem',
  color: 'var(--text-secondary)',
  marginTop: '4px',
  lineHeight: '1.4'
};

const notifCardTimeStyle = {
  fontSize: '0.74rem',
  color: 'var(--text-muted)',
  display: 'block',
  marginTop: '6px'
};

const notifCardReadBtn = {
  padding: '6px 12px',
  fontSize: '0.74rem',
  height: '30px'
};

const roleBadgeStyle = (roleName) => {
  let bg = 'rgba(79, 70, 229, 0.08)';
  let color = '#4f46e5';
  if (roleName === 'Administrator') {
    bg = 'rgba(225, 29, 72, 0.08)';
    color = '#e11d48';
  } else if (roleName === 'Marketing Team') {
    bg = 'rgba(5, 150, 105, 0.08)';
    color = '#059669';
  } else if (roleName === 'Content Creator') {
    bg = 'rgba(147, 51, 234, 0.08)';
    color = '#9333ea';
  }
  return {
    padding: '4px 8px',
    borderRadius: '6px',
    fontSize: '0.78rem',
    fontWeight: '600',
    backgroundColor: bg,
    color: color
  };
};

const actionBadgeStyle = (action) => {
  const isLogin = action === 'LOGIN';
  return {
    padding: '4px 8px',
    borderRadius: '6px',
    fontSize: '0.78rem',
    fontWeight: '600',
    backgroundColor: isLogin ? 'rgba(5, 150, 105, 0.08)' : 'rgba(71, 85, 105, 0.08)',
    color: isLogin ? '#059669' : '#475569'
  };
};

export default Dashboard;

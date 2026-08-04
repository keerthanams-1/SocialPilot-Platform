import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { 
  FiFolder, FiPlus, FiTrash2, FiClock, FiDollarSign, FiTarget, 
  FiAlertCircle, FiCheckCircle, FiFileText, FiChevronDown, FiChevronUp,
  FiLink, FiCheck, FiX
} from 'react-icons/fi';

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [allPosts, setAllPosts] = useState([]);
  const [teamId, setTeamId] = useState('');
  const [loading, setLoading] = useState(true);
  
  // Create Campaign Modal/Form States
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [budget, setBudget] = useState('');
  const [objectives, setObjectives] = useState('');
  
  const [showWizard, setShowWizard] = useState(false);
  const [expandedCampaignId, setExpandedCampaignId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Assign Posts Modal States
  const [assignModalCampaignId, setAssignModalCampaignId] = useState(null);
  const [selectedPostIds, setSelectedPostIds] = useState([]);

  // 1. Resolve active team workspace
  const getActiveTeamId = useCallback(() => {
    return localStorage.getItem('socialpilot_active_team_id') || '';
  }, []);

  // 2. Fetch campaigns list & posts
  const loadCampaigns = useCallback(async (activeId) => {
    const currentId = activeId || teamId;
    if (!currentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [campaignsRes, postsRes] = await Promise.all([
        api.get(`/campaigns?team_id=${currentId}`),
        api.get(`/posts?team_id=${currentId}`)
      ]);
      const camps = Array.isArray(campaignsRes.data) ? campaignsRes.data : (campaignsRes.data?.data?.campaigns || campaignsRes.data?.data || []);
      const psts = Array.isArray(postsRes.data) ? postsRes.data : (postsRes.data?.data?.posts || postsRes.data?.data || []);
      setCampaigns(camps);
      setAllPosts(psts);
    } catch (err) {
      setError('Failed to fetch campaigns and posts.');
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    const id = getActiveTeamId();
    if (id) {
      setTeamId(id);
      loadCampaigns(id);
    } else {
      setLoading(false);
    }
  }, [getActiveTeamId, loadCampaigns]);

  // Set default dates (today and one week from today)
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const nextWeekStr = nextWeek.toISOString().split('T')[0];
    setStartDate(today);
    setEndDate(nextWeekStr);
  }, []);

  // 3. Handle Campaign Submission
  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim()) {
      setError('Campaign name cannot be empty.');
      return;
    }

    if (new Date(endDate) < new Date(startDate)) {
      setError('Campaign end date cannot be earlier than its start date.');
      return;
    }

    try {
      const payload = {
        team_id: teamId,
        name: name.trim(),
        description: description.trim() || null,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        budget: budget ? parseFloat(budget) : null,
        objectives: objectives.trim() || null
      };

      await api.post('/campaigns', payload);
      setSuccess(`Campaign "${name}" initialized successfully!`);
      
      // Reset form fields
      setName('');
      setDescription('');
      setBudget('');
      setObjectives('');
      setShowWizard(false);
      
      // Reload lists
      loadCampaigns(teamId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initialize campaign.');
    }
  };

  const handleDeleteCampaign = async (id, cName) => {
    if (!window.confirm(`Are you sure you want to delete "${cName}"? Linked posts will be unlinked (preserved as standalone posts).`)) {
      return;
    }
    setError('');
    setSuccess('');
    try {
      await api.delete(`/campaigns/${id}`);
      setSuccess(`Campaign "${cName}" deleted.`);
      setCampaigns(prev => prev.filter(c => c.id !== id));
      if (expandedCampaignId === id) setExpandedCampaignId(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete campaign.');
    }
  };

  // 4. Assign Post Handlers
  const handleOpenAssignModal = (campaignId) => {
    setAssignModalCampaignId(campaignId);
    setSelectedPostIds([]);
  };

  const handleCloseAssignModal = () => {
    setAssignModalCampaignId(null);
    setSelectedPostIds([]);
  };

  const handleTogglePostSelect = (postId) => {
    setSelectedPostIds(prev => 
      prev.includes(postId) 
        ? prev.filter(id => id !== postId) 
        : [...prev, postId]
    );
  };

  const handleSaveAssignments = async () => {
    if (selectedPostIds.length === 0 || !assignModalCampaignId) return;
    setError('');
    setSuccess('');
    try {
      const response = await api.post(`/campaigns/${assignModalCampaignId}/assign-posts`, {
        post_ids: selectedPostIds
      });
      
      const msg = response.data?.message || `Successfully assigned ${selectedPostIds.length} posts to campaign.`;
      setSuccess(msg);
      handleCloseAssignModal();
      loadCampaigns(teamId);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to save post assignments.');
    }
  };

  const toggleExpandCampaign = (id) => {
    setExpandedCampaignId(prev => prev === id ? null : id);
  };

  const getPostStatusBadge = (status) => {
    let color = 'var(--text-secondary)';
    if (status === 'published') color = 'var(--success)';
    else if (status === 'failed') color = 'var(--error)';
    else if (status === 'scheduled') color = 'var(--warning)';
    return <span style={{ ...miniStatusStyle, color }}>{status.toUpperCase()}</span>;
  };

  // 5. Timeline Layout Sub-renderer
  const renderTimeline = (campaign) => {
    const start = new Date(campaign.start_date);
    const end = new Date(campaign.end_date);
    const today = new Date();
    
    const totalDuration = end.getTime() - start.getTime();
    if (totalDuration <= 0) return null;

    let todayPercent = 0;
    if (today >= start && today <= end) {
      todayPercent = ((today.getTime() - start.getTime()) / totalDuration) * 100;
    } else if (today > end) {
      todayPercent = 100;
    }
    
    const campaignPosts = (campaign.posts || [])
      .filter(p => p.scheduled_at)
      .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));

    return (
      <div style={timelineContainerStyle}>
        <h4 style={expandedHeaderTitleStyle}>Campaign Timeline</h4>
        <div style={timelineTrackStyle}>
          <div style={timelineLineStyle}>
            <div style={timelineProgressFillStyle(todayPercent)}></div>
          </div>
          
          {today >= start && today <= end && (
            <div 
              style={todayPinStyle(todayPercent)} 
              title={`Today: ${today.toLocaleDateString()}`}
            >
              <div style={todayLabelStyle}>Today</div>
            </div>
          )}
          
          <div style={endpointPinStyle(0)} title={`Start Date: ${start.toLocaleDateString()}`}>
            <div style={endpointDotStyle}></div>
            <div style={endpointLabelStyle}>Start ({start.toLocaleDateString()})</div>
          </div>
          
          <div style={endpointPinStyle(100)} title={`End Date: ${end.toLocaleDateString()}`}>
            <div style={endpointDotStyle}></div>
            <div style={endpointLabelStyle}>End ({end.toLocaleDateString()})</div>
          </div>
          
          {campaignPosts.map(p => {
            const pDate = new Date(p.scheduled_at);
            let pPercent = ((pDate.getTime() - start.getTime()) / totalDuration) * 100;
            if (pPercent < 0) pPercent = 0;
            if (pPercent > 100) pPercent = 100;
            
            return (
              <div 
                key={p.id} 
                style={milestonePinStyle(pPercent)} 
                title={`${p.status.toUpperCase()} - ${pDate.toLocaleString()}: ${p.content_text}`}
              >
                <div style={milestoneDotStyle(p.status)}></div>
                <div style={milestoneLabelStyle}>
                  {pDate.toLocaleDateString()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (loading) {
    return <div style={centerTextStyle}>Syncing marketing campaigns...</div>;
  }

  if (!teamId) {
    return (
      <div className="glass-panel animate-fade-in" style={noWorkspaceStyle}>
        <FiAlertCircle size={40} style={{ color: 'var(--warning)', marginBottom: '16px' }} />
        <h3>No Team Workspace Active</h3>
        <p>Go to the **Team Workspace** panel to launch a workspace before setting up marketing campaigns.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={headerRowStyle}>
        <div>
          <h2 style={sectionTitleStyle}>Marketing Campaigns</h2>
          <p style={sectionDescStyle}>Group scheduled posts, set objectives, and track active campaign performance.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowWizard(prev => !prev)} style={createCampaignBtnStyle}>
          <FiPlus /> {showWizard ? 'View Campaigns' : 'New Campaign'}
        </button>
      </div>

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

      {/* Create Campaign form wizard */}
      {showWizard ? (
        <div className="glass-panel animate-fade-in" style={panelContainerStyle}>
          <h3 style={wizardTitleStyle}>Initialize Marketing Campaign</h3>
          <p style={wizardDescStyle}>Set target goals, allocations, and durations to organize scheduling queues.</p>
          
          <form onSubmit={handleCreateCampaign} style={formStyle}>
            <div style={formRowStyle}>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Campaign Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Q3 Summer Product Launch"
                  style={inputStyle}
                  required
                />
              </div>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Budget (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="e.g. 5000.00"
                  style={inputStyle}
                />
              </div>
            </div>

            <div style={formRowStyle}>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={inputStyle}
                  required
                />
              </div>
              <div style={formGroupStyle}>
                <label style={labelStyle}>End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={inputStyle}
                  required
                />
              </div>
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Campaign Objectives</label>
              <input
                type="text"
                value={objectives}
                onChange={(e) => setObjectives(e.target.value)}
                placeholder="e.g. Boost conversions by 15% and increase social footprint by 5k followers."
                style={inputStyle}
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Brief Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Summary description for digital marketing assets, tags, and audience groups..."
                style={textareaStyle}
              />
            </div>

            <button type="submit" className="btn-primary" style={submitBtnStyle}>
              Initialize Campaign
            </button>
          </form>
        </div>
      ) : (
        /* Campaigns Queue List */
        <div>
          {campaigns.length === 0 ? (
            <div className="glass-panel" style={emptyStateStyle}>
              <FiFolder size={44} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
              <h3>No Marketing Campaigns Yet</h3>
              <p>Initialize a campaign using the button above to start grouping scheduled posts.</p>
            </div>
          ) : (
            <div style={campaignsListStyle}>
              {campaigns.map(c => {
                const isExpanded = expandedCampaignId === c.id;
                const totalPosts = c.posts?.length || 0;
                const publishedPosts = c.posts?.filter(p => p.status === 'published').length || 0;
                const progressRate = totalPosts > 0 ? (publishedPosts / totalPosts) * 100 : 0;
                
                return (
                  <div key={c.id} style={campaignCardStyle} className="glass-panel">
                    
                    <div style={campaignHeaderRowStyle}>
                      <div>
                        <div style={titleBadgeRow}>
                          <h3 style={campaignTitleStyle}>{c.name}</h3>
                          <span style={activeStatusBadge}>{c.status.toUpperCase()}</span>
                        </div>
                        <span style={dateRangeTextStyle}>
                          <FiClock size={12} /> {new Date(c.start_date).toLocaleDateString()} – {new Date(c.end_date).toLocaleDateString()}
                        </span>
                      </div>
                      
                      <div style={headerActionsGroup}>
                        <button 
                          className="btn-primary"
                          style={assignBtnStyle}
                          onClick={() => handleOpenAssignModal(c.id)}
                        >
                          <FiLink /> Assign Posts
                        </button>
                        
                        <button 
                          className="btn-secondary" 
                          style={expandBtnStyle} 
                          onClick={() => toggleExpandCampaign(c.id)}
                        >
                          {isExpanded ? <FiChevronUp /> : <FiChevronDown />} {isExpanded ? 'Hide' : 'View Details'} ({totalPosts})
                        </button>
                        
                        <button 
                          className="btn-danger" 
                          style={deleteBtnStyle}
                          onClick={() => handleDeleteCampaign(c.id, c.name)}
                        >
                          <FiTrash2 size={15} />
                        </button>
                      </div>
                    </div>

                    {/* Meta statistics section */}
                    <div style={campaignStatsGridStyle}>
                      <div style={metaCardStyle} className="glass-panel">
                        <FiTarget size={18} style={{ color: 'var(--primary)' }} />
                        <div>
                          <span style={metaLabelStyle}>Objectives</span>
                          <span style={metaValueStyle}>{c.objectives || 'None defined'}</span>
                        </div>
                      </div>

                      <div style={metaCardStyle} className="glass-panel">
                        <FiDollarSign size={18} style={{ color: 'var(--success)' }} />
                        <div>
                          <span style={metaLabelStyle}>Budget Allocation</span>
                          <span style={metaValueStyle}>{c.budget ? `$${c.budget.toLocaleString()}` : 'No limit set'}</span>
                        </div>
                      </div>

                      <div style={metaCardStyle} className="glass-panel">
                        <FiFileText size={18} style={{ color: 'var(--warning)' }} />
                        <div>
                          <span style={metaLabelStyle}>Content Queue</span>
                          <span style={metaValueStyle}>{publishedPosts}/{totalPosts} published</span>
                        </div>
                      </div>
                    </div>

                    {/* Progress Slider */}
                    {totalPosts > 0 && (
                      <div style={progressSectionStyle}>
                        <div style={progressLabelRow}>
                          <span>Campaign Completion Rate</span>
                          <span>{Math.round(progressRate)}%</span>
                        </div>
                        <div style={progressBarBg}>
                          <div style={progressBarFill(progressRate)}></div>
                        </div>
                      </div>
                    )}

                    {/* Detailed Strategy, Timeline, Team Collaborators and Associated Posts */}
                    {isExpanded && (
                      <div style={expandedPostsContainerStyle} className="animate-fade-in">
                        
                        {/* Brief Description & Target Persona Grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left' }}>
                            <h5 style={{ margin: '0 0 8px 0', fontSize: '0.88rem', color: 'var(--primary)' }}>📌 Campaign Strategy Brief</h5>
                            <p style={{ margin: '0 0 8px 0', fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                              {c.description || 'Enterprise multi-channel digital marketing campaign targeting audience engagement, brand awareness, and lead conversion.'}
                            </p>
                            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                              🎯 <b>Target Demographic</b>: Age 25–45 \| Enterprise IT Executives & Digital Marketers
                            </div>
                          </div>

                          <div className="glass-panel" style={{ padding: '16px', textAlign: 'left' }}>
                            <h5 style={{ margin: '0 0 8px 0', fontSize: '0.88rem', color: 'var(--success)' }}>👥 Assigned Collaborators</h5>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', marginTop: '6px' }}>
                              <span style={{ fontSize: '0.78rem', background: 'rgba(99, 102, 241, 0.15)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-primary)' }}>
                                👤 Sarah Jenkins (Business Mgr)
                              </span>
                              <span style={{ fontSize: '0.78rem', background: 'rgba(16, 185, 129, 0.15)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-primary)' }}>
                                ✍️ Alex Rivera (Senior Creator)
                              </span>
                              <span style={{ fontSize: '0.78rem', background: 'rgba(245, 158, 11, 0.15)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-primary)' }}>
                                📣 Elena Rostova (Marketing Lead)
                              </span>
                              <span style={{ fontSize: '0.78rem', background: 'rgba(236, 72, 153, 0.15)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-primary)' }}>
                                📊 David Miller (Analytics Lead)
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* KPI Performance Targets Grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                          <div className="glass-panel" style={{ padding: '12px', textAlign: 'left', borderRadius: '10px' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target Impressions</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--primary)', marginTop: '2px' }}>500,000</div>
                          </div>
                          <div className="glass-panel" style={{ padding: '12px', textAlign: 'left', borderRadius: '10px' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target Clicks</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--success)', marginTop: '2px' }}>25,000</div>
                          </div>
                          <div className="glass-panel" style={{ padding: '12px', textAlign: 'left', borderRadius: '10px' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conversion Rate</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--warning)', marginTop: '2px' }}>4.85%</div>
                          </div>
                          <div className="glass-panel" style={{ padding: '12px', textAlign: 'left', borderRadius: '10px' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Expected ROI</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#ec4899', marginTop: '2px' }}>450%</div>
                          </div>
                        </div>

                        {renderTimeline(c)}
                        
                        <h4 style={expandedHeaderTitleStyle}>Grouped Publishing Queue</h4>
                        {totalPosts === 0 ? (
                          <p style={emptyExpandedTextStyle}>No posts scheduled under this campaign. Click **Assign Posts** or go to the Scheduler to compose campaign content.</p>
                        ) : (
                          <div style={expandedPostsListStyle}>
                            {c.posts.map(p => (
                              <div key={p.id} style={miniPostItemStyle} className="glass-panel">
                                <div style={miniPostContentRow}>
                                  <p style={miniPostTextStyle}>"{p.content_text}"</p>
                                  {getPostStatusBadge(p.status)}
                                </div>
                                <span style={miniPostTimeStyle}>
                                  {p.scheduled_at ? `Scheduled: ${new Date(p.scheduled_at).toLocaleString()}` : 'Saved Draft'}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Assign Posts Overlay Modal */}
      {assignModalCampaignId && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle} className="glass-panel animate-fade-in">
            <h3 style={modalTitleStyle}>Assign Content Posts</h3>
            <p style={modalDescStyle}>Select unassigned posts from your active workspace schedule to map to this campaign.</p>
            
            <div style={unassignedPostsContainer}>
              {allPosts.filter(p => p.campaign_id !== assignModalCampaignId).length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  All workspace posts have already been assigned to this campaign or other campaigns.
                </div>
              ) : (
                <div style={unassignedPostsGrid}>
                  {allPosts
                    .filter(p => p.campaign_id !== assignModalCampaignId)
                    .map(p => {
                      const isSelected = selectedPostIds.includes(p.id);
                      return (
                        <div 
                          key={p.id} 
                          style={unassignedPostCard(isSelected)} 
                          onClick={() => handleTogglePostSelect(p.id)}
                        >
                          <input 
                            type="checkbox" 
                            checked={isSelected}
                            onChange={() => {}}
                            style={{ pointerEvents: 'none' }}
                          />
                          <div style={{ flex: 1 }}>
                            <p style={unassignedPostText}>"{p.content_text.substring(0, 100)}{p.content_text.length > 100 ? '...' : ''}"</p>
                            <span style={unassignedPostMeta}>
                              Scheduled: {p.scheduled_at ? new Date(p.scheduled_at).toLocaleString() : 'Saved Draft'} | Status: {p.status.toUpperCase()}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                </div>
              )}
            </div>

            <div style={modalActionsStyle}>
              <button className="btn-secondary" onClick={handleCloseAssignModal} style={{ height: '36px', fontSize: '0.82rem' }}>
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={handleSaveAssignments}
                disabled={selectedPostIds.length === 0}
                style={{ height: '36px', fontSize: '0.82rem' }}
              >
                Save Assignments ({selectedPostIds.length})
              </button>
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

const createCampaignBtnStyle = {
  padding: '10px 20px',
  fontSize: '0.85rem'
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

const successContainerStyle = {
  background: 'rgba(16, 185, 129, 0.1)',
  border: '1px solid rgba(16, 185, 129, 0.2)',
  borderRadius: '10px',
  color: 'var(--success)',
  padding: '12px 16px',
  marginBottom: '24px',
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  fontSize: '0.85rem'
};

const panelContainerStyle = {
  padding: '32px',
  maxWidth: '800px',
  margin: '0 auto'
};

const wizardTitleStyle = {
  fontSize: '1.25rem',
  marginBottom: '4px'
};

const wizardDescStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  marginBottom: '24px'
};

const formStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '20px'
};

const formRowStyle = {
  display: 'flex',
  gap: '20px'
};

const formGroupStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  gap: '8px'
};

const labelStyle = {
  fontSize: '0.85rem',
  fontWeight: '600',
  color: 'var(--text-secondary)'
};

const inputStyle = {
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  padding: '10px 16px',
  color: 'var(--text-primary)',
  fontSize: '0.9rem',
  outline: 'none'
};

const textareaStyle = {
  ...inputStyle,
  minHeight: '100px',
  resize: 'vertical',
  fontFamily: 'inherit'
};

const submitBtnStyle = {
  padding: '12px 24px',
  fontSize: '0.9rem',
  alignSelf: 'start',
  marginTop: '8px'
};

const emptyStateStyle = {
  padding: '64px 32px',
  textAlign: 'center',
  color: 'var(--text-muted)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
};

const campaignsListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '24px'
};

const campaignCardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
  gap: '20px',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
  background: 'rgba(255, 255, 255, 0.01)'
};

const campaignHeaderRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'start',
  gap: '16px',
  borderBottom: '1px solid var(--border-color)',
  paddingBottom: '16px'
};

const titleBadgeRow = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  flexWrap: 'wrap'
};

const campaignTitleStyle = {
  fontSize: '1.25rem',
  fontWeight: '600'
};

const activeStatusBadge = {
  fontSize: '0.72rem',
  background: 'rgba(16, 185, 129, 0.1)',
  color: 'var(--success)',
  padding: '2px 8px',
  borderRadius: '10px',
  fontWeight: '600'
};

const dateRangeTextStyle = {
  fontSize: '0.8rem',
  color: 'var(--text-secondary)',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  marginTop: '4px'
};

const headerActionsGroup = {
  display: 'flex',
  gap: '12px',
  alignItems: 'center'
};

const assignBtnStyle = {
  padding: '8px 16px',
  fontSize: '0.8rem',
  height: '36px',
  display: 'flex',
  alignItems: 'center',
  gap: '6px'
};

const expandBtnStyle = {
  padding: '8px 16px',
  fontSize: '0.8rem',
  height: '36px',
  display: 'flex',
  alignItems: 'center',
  gap: '6px'
};

const deleteBtnStyle = {
  padding: '8px 12px',
  height: '36px'
};

const campaignStatsGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
  gap: '16px'
};

const metaCardStyle = {
  padding: '16px',
  borderRadius: '10px',
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  background: 'rgba(255,255,255,0.01)'
};

const metaLabelStyle = {
  display: 'block',
  fontSize: '0.74rem',
  color: 'var(--text-muted)',
  fontWeight: '500'
};

const metaValueStyle = {
  display: 'block',
  fontSize: '0.88rem',
  fontWeight: '600',
  color: 'var(--text-secondary)',
  marginTop: '2px'
};

const progressSectionStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px'
};

const progressLabelRow = {
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '0.8rem',
  color: 'var(--text-secondary)',
  fontWeight: '500'
};

const progressBarBg = {
  width: '100%',
  height: '8px',
  borderRadius: '4px',
  background: 'rgba(255,255,255,0.05)',
  overflow: 'hidden'
};

const progressBarFill = (rate) => ({
  width: `${rate}%`,
  height: '100%',
  background: 'linear-gradient(90deg, var(--primary) 0%, var(--success) 100%)',
  borderRadius: '4px',
  transition: 'width 0.6s ease-in-out'
});

const expandedPostsContainerStyle = {
  borderTop: '1px solid var(--border-color)',
  paddingTop: '20px',
  marginTop: '4px'
};

const expandedHeaderTitleStyle = {
  fontSize: '0.92rem',
  fontWeight: '600',
  marginBottom: '12px',
  color: 'var(--text-secondary)'
};

const emptyExpandedTextStyle = {
  fontSize: '0.8rem',
  color: 'var(--text-muted)',
  fontStyle: 'italic'
};

const expandedPostsListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '10px'
};

const miniPostItemStyle = {
  padding: '12px 16px',
  borderRadius: '8px',
  background: 'rgba(255,255,255,0.005)'
};

const miniPostContentRow = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '16px'
};

const miniPostTextStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  wordBreak: 'break-word',
  flex: 1
};

const miniStatusStyle = {
  fontSize: '0.7rem',
  fontWeight: '600',
  padding: '2px 6px',
  borderRadius: '4px',
  background: 'rgba(255,255,255,0.02)'
};

const miniPostTimeStyle = {
  fontSize: '0.74rem',
  color: 'var(--text-muted)',
  display: 'block',
  marginTop: '4px'
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

const centerTextStyle = {
  textAlign: 'center',
  padding: '40px',
  color: 'var(--text-secondary)'
};

// Timeline Visual Component Styles
const timelineContainerStyle = {
  marginTop: '16px',
  marginBottom: '40px',
  padding: '16px',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  background: 'rgba(255, 255, 255, 0.005)'
};

const timelineTrackStyle = {
  position: 'relative',
  height: '75px',
  marginTop: '32px',
  padding: '0 24px'
};

const timelineLineStyle = {
  position: 'absolute',
  top: '20px',
  left: '24px',
  right: '24px',
  height: '6px',
  background: 'rgba(255,255,255,0.05)',
  borderRadius: '3px'
};

const timelineProgressFillStyle = (percent) => ({
  width: `${percent}%`,
  height: '100%',
  background: 'var(--primary)',
  borderRadius: '3px',
  opacity: 0.7
});

const endpointPinStyle = (percent) => ({
  position: 'absolute',
  left: `${percent}%`,
  transform: 'translateX(-50%)',
  top: '14px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  zIndex: 2
});

const endpointDotStyle = {
  width: '18px',
  height: '18px',
  borderRadius: '50%',
  background: '#111122',
  border: '3px solid var(--text-muted)',
  boxShadow: '0 0 10px rgba(0,0,0,0.5)'
};

const endpointLabelStyle = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  marginTop: '8px',
  whiteSpace: 'nowrap'
};

const todayPinStyle = (percent) => ({
  position: 'absolute',
  left: `${percent}%`,
  transform: 'translateX(-50%)',
  top: '4px',
  height: '36px',
  width: '4px',
  background: 'var(--warning)',
  zIndex: 3
});

const todayLabelStyle = {
  position: 'absolute',
  top: '-20px',
  left: '50%',
  transform: 'translateX(-50%)',
  fontSize: '0.64rem',
  fontWeight: '700',
  color: 'var(--warning)',
  background: 'rgba(245, 158, 11, 0.1)',
  padding: '1px 4px',
  borderRadius: '3px',
  whiteSpace: 'nowrap'
};

const milestonePinStyle = (percent) => ({
  position: 'absolute',
  left: `${percent}%`,
  transform: 'translateX(-50%)',
  top: '15px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  zIndex: 4,
  cursor: 'pointer'
});

const milestoneDotStyle = (status) => {
  let color = 'var(--text-secondary)';
  if (status === 'published') color = 'var(--success)';
  else if (status === 'failed') color = 'var(--error)';
  else if (status === 'scheduled') color = 'var(--warning)';
  
  return {
    width: '14px',
    height: '14px',
    borderRadius: '50%',
    background: color,
    border: '2.5px solid #111122',
    boxShadow: '0 0 8px rgba(0,0,0,0.5)',
    transition: 'transform 0.2s'
  };
};

const milestoneLabelStyle = {
  fontSize: '0.64rem',
  color: 'var(--text-secondary)',
  marginTop: '10px',
  whiteSpace: 'nowrap'
};

// Modal Overlay Styles
const modalOverlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(0, 0, 0, 0.65)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 1000,
  backdropFilter: 'blur(4px)'
};

const modalContentStyle = {
  width: '90%',
  maxWidth: '650px',
  maxHeight: '85vh',
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
  overflowY: 'auto'
};

const modalTitleStyle = {
  fontSize: '1.25rem',
  fontWeight: '600'
};

const modalDescStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  marginBottom: '8px'
};

const unassignedPostsContainer = {
  flex: 1,
  overflowY: 'auto',
  maxHeight: '400px',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  padding: '8px'
};

const unassignedPostsGrid = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px'
};

const unassignedPostCard = (selected) => ({
  display: 'flex',
  alignItems: 'center',
  gap: '16px',
  padding: '12px 16px',
  borderRadius: '8px',
  background: selected ? 'rgba(99, 102, 241, 0.04)' : 'rgba(255, 255, 255, 0.005)',
  border: selected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
  cursor: 'pointer',
  transition: 'all 0.2s ease'
});

const unassignedPostText = {
  fontSize: '0.85rem',
  color: 'var(--text-primary)',
  fontWeight: '500',
  lineHeight: '1.4',
  textAlign: 'left'
};

const unassignedPostMeta = {
  fontSize: '0.74rem',
  color: 'var(--text-muted)',
  display: 'block',
  marginTop: '4px',
  textAlign: 'left'
};

const modalActionsStyle = {
  display: 'flex',
  justifyContent: 'flex-end',
  gap: '12px',
  marginTop: '8px'
};

export default Campaigns;

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import DevicePreviewModal from '../../components/DevicePreviewModal';
import { 
  FiLayout, FiUser, FiUsers, FiCalendar, FiFolder, FiBarChart2, 
  FiSettings, FiLogOut, FiMenu, FiLink, FiBell, FiCheckCircle, 
  FiAlertCircle, FiInfo, FiEdit3, FiLayers, FiTrash2, FiSend, 
  FiRefreshCw, FiClock, FiPlus, FiChevronDown, FiChevronUp, 
  FiFileText, FiImage, FiUpload, FiThumbsUp, FiMessageCircle, FiShare2, FiSmartphone 
} from 'react-icons/fi';
import { FaLinkedinIn, FaFacebookF, FaInstagram } from 'react-icons/fa';

const Scheduler = ({ initialTab }) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(initialTab || 'compose');
  const [showDevicePreviewModal, setShowDevicePreviewModal] = useState(false);
  const isCreator = user?.role?.name === 'Content Creator';

  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  const [posts, setPosts] = useState([]);
  const [channels, setChannels] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [teamId, setTeamId] = useState('');
  
  // Compose Form states
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [content, setContent] = useState('');
  const [mediaUrls, setMediaUrls] = useState([]);
  const [currentMediaUrl, setCurrentMediaUrl] = useState('');
  const [scheduleType, setScheduleType] = useState('scheduled'); // scheduled, draft, recurring
  const [recurrencePattern, setRecurrencePattern] = useState('daily');
  const [scheduleTime, setScheduleTime] = useState('');
  const [selectedCampaignId, setSelectedCampaignId] = useState('');

  // Local Live Preview state
  const [previewPlatform, setPreviewPlatform] = useState('linkedin'); // linkedin, facebook, instagram

  // Queue Management states
  const [queueFilter, setQueueFilter] = useState('all'); // all, scheduled, draft, published, failed
  const [expandedPostHistoryId, setExpandedPostHistoryId] = useState(null);

  // Calendar states
  const [currentDate, setCurrentDate] = useState(new Date());

  // Quick Add Calendar Modal states
  const [isCalendarModalOpen, setIsCalendarModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState(null);
  const [modalContent, setModalContent] = useState('');
  const [modalSelectedChannels, setModalSelectedChannels] = useState([]);
  const [modalScheduleTime, setModalScheduleTime] = useState('');
  const [modalMediaUrl, setModalMediaUrl] = useState('');
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  // General message alerts
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  const [channelsLoading, setChannelsLoading] = useState(true);

  // 1. Resolve active team workspace
  const getActiveTeamId = useCallback(() => {
    return localStorage.getItem('socialpilot_active_team_id') || '';
  }, []);

  const loadChannels = useCallback(async (activeId) => {
    const defaultDemo = [
      { id: "ch_linkedin", platform: "linkedin", account_name: "SocialPilot Enterprise LinkedIn Page", status: "connected", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=LinkedInPage" },
      { id: "ch_instagram", platform: "instagram", account_name: "@socialpilot_official", status: "connected", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=InstagramBrand" },
      { id: "ch_facebook", platform: "facebook", account_name: "SocialPilot Official Meta Business Page", status: "connected", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=MetaPage" },
      { id: "ch_twitter", platform: "twitter", account_name: "@SocialPilotApp", status: "connected", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=TwitterApp" },
      { id: "ch_youtube", platform: "youtube", account_name: "SocialPilot Tech & Tutorials", status: "connected", avatar_url: "https://api.dicebear.com/7.x/initials/svg?seed=YouTubeChannel" }
    ];

    setChannelsLoading(true);
    try {
      if (activeId) {
        const response = await api.get(`/social/accounts?team_id=${activeId}`);
        const chs = Array.isArray(response.data) ? response.data : (response.data?.data?.accounts || response.data?.data || []);
        if (Array.isArray(chs) && chs.length > 0) {
          setChannels(chs);
          return;
        }
      }
      setChannels(defaultDemo);
    } catch (err) {
      setChannels(defaultDemo);
    } finally {
      setChannelsLoading(false);
    }
  }, []);

  const loadPosts = useCallback(async (activeId) => {
    const currentId = activeId || teamId;
    if (!currentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await api.get(`/posts?team_id=${currentId}`);
      const psts = Array.isArray(response.data) ? response.data : (response.data?.data?.posts || response.data?.data || []);
      setPosts(psts);
    } catch (err) {
      setError('Failed to fetch scheduled posts.');
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  const loadCampaigns = useCallback(async (activeId) => {
    const currentId = activeId || teamId;
    if (!currentId) return;
    try {
      const response = await api.get(`/campaigns?team_id=${currentId}`);
      const camps = Array.isArray(response.data) ? response.data : (response.data?.data?.campaigns || response.data?.data || []);
      setCampaigns(camps);
    } catch (err) {
      console.error('Failed to load campaigns list', err);
    }
  }, [teamId]);

  useEffect(() => {
    const id = getActiveTeamId();
    if (id) {
      setTeamId(id);
      loadChannels(id);
      loadPosts(id);
      loadCampaigns(id);

      // Real-time silent background poll every 5 seconds to update post status
      const interval = setInterval(() => {
        const reloadPostsSilently = async () => {
          try {
            const response = await api.get(`/posts?team_id=${id}`);
            setPosts(response.data);
          } catch (err) {
            console.error('Failed to silent reload posts', err);
          }
        };
        reloadPostsSilently();
      }, 5000);

      return () => clearInterval(interval);
    } else {
      setLoading(false);
      setChannelsLoading(false);
    }
  }, [getActiveTeamId, loadChannels, loadPosts, loadCampaigns]);

  // Set default publishing time (now + 1 hour)
  useEffect(() => {
    const now = new Date();
    now.setHours(now.getHours() + 1);
    // Format to yyyy-MM-ddThh:mm matching input type=datetime-local
    const tzOffset = now.getTimezoneOffset() * 60000;
    const localISOTime = new Date(now - tzOffset).toISOString().slice(0, 16);
    setScheduleTime(localISOTime);
  }, []);

  const openCalendarModal = (day) => {
    if (!day) return;
    const year = day.getFullYear();
    const month = String(day.getMonth() + 1).padStart(2, '0');
    const dateStr = String(day.getDate()).padStart(2, '0');
    const isoTime = `${year}-${month}-${dateStr}T10:00`;
    
    setModalDate(day);
    setModalScheduleTime(isoTime);
    setModalContent('');
    setModalMediaUrl('');
    setModalError('');
    const defaultChs = channels.length > 0 ? channels.map(c => c.id || c.platform) : ['facebook', 'instagram', 'linkedin', 'twitter'];
    setModalSelectedChannels(defaultChs);
    setIsCalendarModalOpen(true);
  };

  const handleModalSavePost = async (e) => {
    e.preventDefault();
    setModalError('');
    if (!modalContent.trim()) {
      setModalError('Please enter post content caption.');
      return;
    }
    
    // Auto-resolve active workspace team ID
    const activeTeamId = teamId || localStorage.getItem('socialpilot_active_team_id') || 'team_enterprise_workspace_default';
    if (!teamId) {
      setTeamId(activeTeamId);
    }

    const targetChannels = modalSelectedChannels.length > 0 
      ? modalSelectedChannels 
      : (channels.length > 0 ? channels.map(c => c.id || c.platform) : ['facebook', 'instagram', 'linkedin', 'twitter']);
    
    setModalSubmitting(true);
    setError('');
    setSuccess('');
    
    try {
      const scheduledIsoDate = new Date(modalScheduleTime).toISOString();
      const payload = {
        team_id: activeTeamId,
        content_text: modalContent.trim(),
        media_urls: modalMediaUrl.trim() ? [modalMediaUrl.trim()] : [],
        platform_targets: targetChannels,
        schedule_type: 'scheduled',
        scheduled_at: scheduledIsoDate
      };
      
      const response = await api.post('/posts', payload);
      const createdPost = response.data?.data || response.data || {
        id: `post_${Date.now()}`,
        team_id: activeTeamId,
        content_text: modalContent.trim(),
        media_urls: modalMediaUrl.trim() ? [modalMediaUrl.trim()] : [],
        platform_targets: targetChannels,
        schedule_type: 'scheduled',
        scheduled_at: scheduledIsoDate,
        status: 'scheduled'
      };

      // 1. Immediately append post into local state for instant calendar rendering
      setPosts(prev => [createdPost, ...prev]);

      // 2. Show prominent success banner
      setSuccess(`Post scheduled for ${new Date(modalScheduleTime).toLocaleDateString()} at ${new Date(modalScheduleTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} successfully!`);

      // 3. Close modal & reset fields
      setIsCalendarModalOpen(false);
      setModalContent('');
      setModalMediaUrl('');

      // 4. Reload from backend DB
      loadPosts(activeTeamId);
    } catch (err) {
      console.error('Failed to schedule post from calendar modal', err);
      const detail = err.response?.data?.detail;
      const errMsg = detail 
        ? (typeof detail === 'string' ? detail : JSON.stringify(detail))
        : (err.response?.data?.message || err.message || 'Failed to schedule post.');
      setModalError(`Backend Error: ${errMsg}`);
      setError(`Backend Error: ${errMsg}`);
    } finally {
      setModalSubmitting(false);
    }
  };

  // 2. Media attachment helpers
  const handleAddMedia = () => {
    if (!currentMediaUrl.trim()) return;
    setMediaUrls(prev => [...prev, currentMediaUrl.trim()]);
    setCurrentMediaUrl('');
  };

  const handleRemoveMedia = (index) => {
    setMediaUrls(prev => prev.filter((_, idx) => idx !== index));
  };

  // Mock File Drag & Drop selector
  const handleFileDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer?.files || e.target?.files;
    if (files && files.length > 0) {
      const file = files[0];
      const simulatedUrl = URL.createObjectURL(file);
      setMediaUrls(prev => [...prev, simulatedUrl]);
    }
  };

  const toggleChannelSelection = (id) => {
    setSelectedChannels(prev => 
      prev.includes(id) ? prev.filter(cId => cId !== id) : [...prev, id]
    );
  };

  // 3. Save / Schedule post submission
  const handleSavePost = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!content.trim()) {
      setError('Post caption cannot be empty.');
      return;
    }

    if (scheduleType !== 'draft' && !scheduleTime) {
      setError('Please specify a target publishing time.');
      return;
    }

    const targetChannels = selectedChannels.length > 0 
      ? selectedChannels 
      : (channels.length > 0 ? channels.map(c => c.id || c.platform) : ['facebook', 'instagram', 'linkedin', 'twitter']);

    try {
      const payload = {
        team_id: teamId,
        content_text: content.trim(),
        media_urls: mediaUrls,
        platform_targets: targetChannels,
        schedule_type: scheduleType,
        recurrence_pattern: scheduleType === 'recurring' ? recurrencePattern : null,
        scheduled_at: scheduleType !== 'draft' ? new Date(scheduleTime).toISOString() : null,
        campaign_id: selectedCampaignId || null
      };

      await api.post('/posts', payload);
      setSuccess(scheduleType === 'draft' ? 'Draft saved successfully!' : 'Post queued successfully!');
      
      // Reset form
      setContent('');
      setMediaUrls([]);
      setSelectedChannels([]);
      setSelectedCampaignId('');
      
      // Reload posts
      loadPosts(teamId);
      setActiveTab('queue');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to schedule post.');
    }
  };

  const handleDeletePost = async (id) => {
    if (!window.confirm('Are you sure you want to remove this post from the scheduling queue?')) {
      return;
    }
    setError('');
    setSuccess('');
    try {
      await api.delete(`/posts/${id}`);
      setSuccess('Post removed.');
      setPosts(prev => prev.filter(p => p.id !== id));
    } catch (err) {
      setError('Failed to delete post.');
    }
  };

  const handlePublishNow = async (id) => {
    setError('');
    setSuccess('');
    try {
      await api.post(`/publishing/dispatch-immediate?post_id=${id}`);
      setSuccess('Publishing request dispatched! Refreshing queue status...');
      loadPosts(teamId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to dispatch post immediately.');
    }
  };

  const handleRetryPost = async (id) => {
    setError('');
    setSuccess('');
    try {
      await api.post(`/publishing/retry?post_id=${id}`);
      setSuccess('Retry dispatch completed! Status updated.');
      loadPosts(teamId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to retry publishing.');
    }
  };

  // 4. Monthly Calendar Math
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const totalDays = new Date(year, month + 1, 0).getDate();
    
    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }
    for (let d = 1; d <= totalDays; d++) {
      days.push(new Date(year, month, d));
    }
    return days;
  };

  const getPostsForDate = (date) => {
    if (!date) return [];
    return posts.filter(post => {
      if (!post.scheduled_at) return false;
      const postDate = new Date(post.scheduled_at);
      return postDate.getDate() === date.getDate() && 
             postDate.getMonth() === date.getMonth() && 
             postDate.getFullYear() === date.getFullYear();
    });
  };

  const handlePrevMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'linkedin': return <FaLinkedinIn style={{ color: '#0a66c2' }} />;
      case 'facebook': return <FaFacebookF style={{ color: '#1877f2' }} />;
      case 'instagram': return <FaInstagram style={{ color: '#e1306c' }} />;
      default: return <FiLink />;
    }
  };

  // 5. Live Mock Preview Switcher Layout
  const renderLiveMockPreview = () => {
    const profilePic = `https://api.dicebear.com/7.x/initials/svg?seed=${user?.name || 'User'}`;
    const firstMedia = mediaUrls.length > 0 ? mediaUrls[0] : null;

    return (
      <div style={previewContainerStyle} className="glass-panel animate-fade-in">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h4 style={{ ...previewTitleStyle, margin: 0 }}>Live Mock Preview</h4>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setShowDevicePreviewModal(true)}
            style={{ height: '30px', fontSize: '0.76rem', display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(99, 102, 241, 0.2)', border: '1px solid var(--primary)' }}
          >
            <FiSmartphone size={14} /> Device Post Preview
          </button>
        </div>
        
        {/* Preview Platform Tab Toggle Buttons */}
        <div style={platformTabsStyle}>
          <button 
            type="button"
            style={previewPlatform === 'linkedin' ? activePlatformTabStyle : platformTabStyle}
            onClick={() => setPreviewPlatform('linkedin')}
          >
            LinkedIn
          </button>
          <button 
            type="button"
            style={previewPlatform === 'facebook' ? activePlatformTabStyle : platformTabStyle}
            onClick={() => setPreviewPlatform('facebook')}
          >
            Facebook
          </button>
          <button 
            type="button"
            style={previewPlatform === 'instagram' ? activePlatformTabStyle : platformTabStyle}
            onClick={() => setPreviewPlatform('instagram')}
          >
            Instagram
          </button>
        </div>

        {/* Dynamic Card based on selected Preview Tab */}
        <div style={mockPostCardStyle}>
          <div style={mockPostHeader}>
            <img src={profilePic} alt="Avatar" style={mockPostAvatar} />
            <div style={mockPostUserRow}>
              <strong style={mockPostName}>{user?.name || 'Anonymous Publisher'}</strong>
              <span style={mockPostMeta}>
                {previewPlatform === 'linkedin' ? 'Professional Network • Just Now' : 'Just Now • 🌐'}
              </span>
            </div>
          </div>

          <div style={mockPostContent}>
            {content || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Write your post caption inside the content editor to view a live simulation...</span>}
          </div>

          {firstMedia && (
            <div style={mockPostImageContainer}>
              <img src={firstMedia} alt="Media Attachment" style={mockPostImage} onError={(e) => {
                // If local URL or broken image URL, fallback gracefully
                e.target.style.display = 'none';
              }} />
            </div>
          )}

          <div style={mockPostActions}>
            <span style={mockPostActionItem}><FiThumbsUp /> Like</span>
            <span style={mockPostActionItem}><FiMessageCircle /> Comment</span>
            <span style={mockPostActionItem}><FiShare2 /> Share</span>
          </div>
        </div>
      </div>
    );
  };

  // 6. Filter Queue logic
  const getFilteredPosts = () => {
    return posts.filter(p => {
      if (queueFilter === 'all') return true;
      if (queueFilter === 'draft') return p.schedule_type === 'draft';
      if (queueFilter === 'scheduled') return p.status === 'scheduled' && p.schedule_type !== 'draft';
      if (queueFilter === 'published') return p.status === 'published';
      if (queueFilter === 'failed') return p.status === 'failed';
      return true;
    });
  };

  if (loading || channelsLoading) {
    return <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>Loading composer components...</div>;
  }

  if (!teamId) {
    return (
      <div className="glass-panel animate-fade-in" style={noWorkspaceStyle}>
        <FiAlertCircle size={40} style={{ color: 'var(--warning)', marginBottom: '16px' }} />
        <h3>No Team Workspace Active</h3>
        <p>Go to the **Team Workspace** panel to launch a workspace before composing content.</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h2 style={sectionTitleStyle}>Content Scheduler</h2>
      <p style={sectionDescStyle}>Plan campaigns, draft media posts, and route publishing queues.</p>

      {/* 7 Standalone Creator Workflow Sub-Tabs */}
      <div style={{ ...tabMenuRowStyle, flexWrap: 'wrap', gap: '8px', marginBottom: '24px' }}>
        <button 
          style={activeTab === 'compose' || activeTab === 'create' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('compose'); setError(''); setSuccess(''); }}
        >
          <FiEdit3 size={15} /> 1. Create New Post
        </button>
        <button 
          style={activeTab === 'media' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('media'); setError(''); setSuccess(''); }}
        >
          <FiImage size={15} /> 2. Upload Media
        </button>
        <button 
          style={activeTab === 'caption' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('caption'); setError(''); setSuccess(''); }}
        >
          <FiFileText size={15} /> 3. Write Copy & Caption
        </button>
        <button 
          style={activeTab === 'channels' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('channels'); setError(''); setSuccess(''); }}
        >
          <FiLink size={15} /> 4. Select Platforms
        </button>
        <button 
          style={activeTab === 'schedule' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('schedule'); setError(''); setSuccess(''); }}
        >
          <FiClock size={15} /> 5. Schedule Date & Preview
        </button>
        <button 
          style={activeTab === 'calendar' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('calendar'); setError(''); setSuccess(''); }}
        >
          <FiCalendar size={15} /> 6. Publishing Calendar
        </button>
        <button 
          style={activeTab === 'queue' ? activeSubTabStyle : subTabStyle}
          onClick={() => { setActiveTab('queue'); setError(''); setSuccess(''); }}
        >
          <FiLayers size={15} /> 7. Queue Management ({posts.length})
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

      {/* MODULE 2: DEDICATED UPLOAD MEDIA MODULE */}
      {activeTab === 'media' && (
        <div className="glass-panel animate-fade-in" style={{ padding: '32px', textAlign: 'left', marginBottom: '24px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🖼️ Module 2: Upload Media & Asset Library
          </h3>
          <p style={{ margin: '0 0 20px 0', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Upload campaign images, videos, and layout assets to attach to social posts.
          </p>

          <div 
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            style={{
              border: '2px dashed var(--primary)',
              borderRadius: '12px',
              padding: '32px',
              textAlign: 'center',
              background: 'rgba(99, 102, 241, 0.05)',
              marginBottom: '20px',
              cursor: 'pointer'
            }}
          >
            <FiUpload size={36} style={{ color: 'var(--primary)', marginBottom: '12px' }} />
            <h4 style={{ margin: '0 0 6px 0', fontSize: '1rem', color: 'var(--text-primary)' }}>Drag and drop media files here</h4>
            <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-muted)' }}>Supports PNG, JPG, MP4, GIF (Max 50MB per asset)</p>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <input 
              type="text" 
              placeholder="Or enter media image URL (e.g. https://images.unsplash.com/...)"
              value={currentMediaUrl}
              onChange={(e) => setCurrentMediaUrl(e.target.value)}
              style={inputStyle}
            />
            <button type="button" className="btn-primary" onClick={handleAddMedia} style={{ padding: '0 20px', whiteSpace: 'nowrap' }}>
              Add Media URL
            </button>
          </div>

          {mediaUrls.length > 0 && (
            <div>
              <h5 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: 'var(--text-primary)' }}>Attached Media Assets ({mediaUrls.length})</h5>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                {mediaUrls.map((url, idx) => (
                  <div key={idx} style={{ position: 'relative', width: '100px', height: '100px', borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
                    <img src={url} alt={`Asset ${idx}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    <button type="button" onClick={() => handleRemoveMedia(idx)} style={{ position: 'absolute', top: 4, right: 4, background: 'rgba(244,63,94,0.9)', color: '#fff', border: 'none', borderRadius: '50%', width: 22, height: 22, cursor: 'pointer', fontSize: '12px' }}>✕</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn-primary" onClick={() => setActiveTab('caption')}>
              Next: Write Caption & Copy ➔
            </button>
          </div>
        </div>
      )}

      {/* MODULE 3: DEDICATED WRITE CAPTION MODULE */}
      {activeTab === 'caption' && (
        <div className="glass-panel animate-fade-in" style={{ padding: '32px', textAlign: 'left', marginBottom: '24px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📝 Module 3: Copywriting & Caption Studio
          </h3>
          <p style={{ margin: '0 0 20px 0', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Draft engaging copy, hashtags, and captions for your multi-channel posts.
          </p>

          <div style={formGroupStyle}>
            <label style={labelStyle}>Post Caption Copy</label>
            <textarea 
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your engaging post caption here... Use hashtags like #SocialPilot #Marketing #SaaS"
              style={textareaStyle}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
              <span>Character Count: {content.length} characters</span>
              <span>Recommended: 100 - 500 chars</span>
            </div>
          </div>

          <div style={{ marginTop: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Quick Hashtags:</span>
            {['#SocialPilot', '#Marketing', '#SaaSGrowth', '#AIAutomation', '#Productivity'].map(tag => (
              <button 
                key={tag}
                type="button" 
                onClick={() => setContent(prev => prev ? `${prev} ${tag}` : tag)}
                style={{ fontSize: '0.78rem', background: 'rgba(99, 102, 241, 0.12)', border: 'none', padding: '4px 10px', borderRadius: '12px', color: 'var(--primary)', cursor: 'pointer' }}
              >
                + {tag}
              </button>
            ))}
          </div>

          <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'space-between' }}>
            <button className="btn-secondary" onClick={() => setActiveTab('media')}>
              ⬅️ Back: Upload Media
            </button>
            <button className="btn-primary" onClick={() => setActiveTab('channels')}>
              Next: Select Platforms ➔
            </button>
          </div>
        </div>
      )}

      {/* MODULE 4: DEDICATED SELECT PLATFORMS MODULE */}
      {activeTab === 'channels' && (
        <div className="glass-panel animate-fade-in" style={{ padding: '32px', textAlign: 'left', marginBottom: '24px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📱 Module 4: Select Target Social Platforms
          </h3>
          <p style={{ margin: '0 0 20px 0', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Choose which connected social channels will receive this publication.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            {['facebook', 'instagram', 'linkedin', 'twitter', 'youtube'].map(p => {
              const isSelected = selectedChannels.includes(p);
              return (
                <div 
                  key={p}
                  onClick={() => {
                    setSelectedChannels(prev => isSelected ? prev.filter(c => c !== p) : [...prev, p]);
                  }}
                  className="glass-panel glass-card-hover"
                  style={{
                    padding: '20px',
                    borderRadius: '12px',
                    cursor: 'pointer',
                    border: isSelected ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                    background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255,255,255,0.02)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}
                >
                  <input type="checkbox" checked={isSelected} onChange={() => {}} style={{ pointerEvents: 'none' }} />
                  <div>
                    <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)', display: 'block', textTransform: 'capitalize' }}>{p}</strong>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Connected Channel</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button className="btn-secondary" onClick={() => setActiveTab('caption')}>
              ⬅️ Back: Write Caption
            </button>
            <button className="btn-primary" onClick={() => setActiveTab('schedule')}>
              Next: Schedule & Preview ➔
            </button>
          </div>
        </div>
      )}

      {/* MODULE 5: DEDICATED SCHEDULE & PREVIEW MODULE */}
      {activeTab === 'schedule' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px', textAlign: 'left' }}>
          <div className="glass-panel animate-fade-in" style={{ padding: '32px' }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '1.2rem', color: 'var(--text-primary)' }}>
              ⏰ Module 5: Schedule Date & Time Picker
            </h3>
            <p style={{ margin: '0 0 20px 0', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              Set your target publishing schedule timestamp.
            </p>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Target Publishing Time</label>
              <input 
                type="datetime-local"
                value={scheduleTime}
                onChange={(e) => setScheduleTime(e.target.value)}
                style={inputStyle}
              />
            </div>

            <div style={formGroupStyle}>
              <label style={labelStyle}>Schedule Type</label>
              <select value={scheduleType} onChange={(e) => setScheduleType(e.target.value)} style={selectStyle}>
                <option value="scheduled">Scheduled Queue Dispatch</option>
                <option value="draft">Save as Work-In-Progress Draft</option>
                <option value="recurring">Recurring Job Schedule</option>
              </select>
            </div>

            <button className="btn-primary" onClick={handleSavePost} style={{ width: '100%', height: '44px', marginTop: '16px' }}>
              🚀 Confirm & Queue Post Publication
            </button>
          </div>

          <div>
            {renderLiveMockPreview()}
          </div>
        </div>
      )}

      {/* TAB CONTENT: COMPOSE & PREVIEW SPLIT PANELS */}
      {activeTab === 'compose' && (
        <div style={composeLayoutGrid}>
          {/* Left panel form */}
          <div className="glass-panel" style={panelContainerStyle}>
            {channels.length === 0 ? (
              <div style={emptyChannelsStyle}>
                <FiAlertCircle size={36} style={{ color: 'var(--warning)', marginBottom: '12px' }} />
                <h4>No Connected Channels Found</h4>
                <p>You must integrate at least one platform channel in the **Social Channels** workspace to start scheduling.</p>
              </div>
            ) : (
              <form onSubmit={handleSavePost} style={formStyle}>
                
                <div style={formGroupStyle}>
                  <label style={labelStyle}>Select Target Platforms</label>
                  <div style={channelsGridStyle}>
                    {channels.map(ch => {
                      const isSelected = selectedChannels.includes(ch.id);
                      const isExpired = ch.status === 'expired';
                      return (
                        <div 
                          key={ch.id} 
                          onClick={() => !isExpired && toggleChannelSelection(ch.id)}
                          style={channelPickerCard(isSelected, isExpired)}
                          className={`glass-panel ${!isExpired ? 'glass-card-hover' : ''}`}
                        >
                          <img src={ch.avatar_url} alt={ch.account_name} style={channelAvatarStyle} />
                          <div style={{ textAlign: 'left' }}>
                            <div style={channelTitleRow}>
                              <span style={channelNameStyle}>{ch.account_name}</span>
                              {getPlatformIcon(ch.platform)}
                            </div>
                            <span style={channelStatusText(isExpired)}>
                              {isExpired ? 'Expired (Locked)' : 'Active Connection'}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div style={formGroupStyle}>
                  <label style={labelStyle}>Content Caption</label>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Write caption... Add hashtags, links and target descriptions..."
                    maxLength={2000}
                    style={textareaStyle}
                  />
                  <span style={charCountStyle}>{content.length}/2000 characters</span>
                </div>

                {/* File Upload Selector and URL input */}
                <div style={formGroupStyle}>
                  <label style={labelStyle}>Upload Media Files or Attach URLs</label>
                  
                  {/* Simulated drag drop file upload box */}
                  <div 
                    style={dragDropAreaStyle} 
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleFileDrop}
                  >
                    <FiUpload size={24} style={{ color: 'var(--primary)', marginBottom: '8px' }} />
                    <span style={dragDropLabel}>Drag & Drop local images here or click to select</span>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleFileDrop} 
                      style={{ position: 'absolute', opacity: 0, width: '100%', height: '100%', cursor: 'pointer', top: 0, left: 0 }}
                    />
                  </div>

                  <div style={mediaInputRow}>
                    <input
                      type="text"
                      value={currentMediaUrl}
                      onChange={(e) => setCurrentMediaUrl(e.target.value)}
                      placeholder="https://example.com/image.png"
                      style={inputStyle}
                    />
                    <button type="button" className="btn-primary" onClick={handleAddMedia} style={addMediaBtnStyle}>
                      Add URL
                    </button>
                  </div>
                  
                  {mediaUrls.length > 0 && (
                    <div style={mediaListStyle}>
                      {mediaUrls.map((url, idx) => (
                        <div key={idx} style={mediaItemStyle} className="glass-panel">
                          <span style={mediaUrlTextStyle}>{url.startsWith('blob:') ? 'Local Selected File' : url}</span>
                          <button type="button" style={mediaRemoveBtn} onClick={() => handleRemoveMedia(idx)}>
                            <FiTrash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div style={schedulingSettingsGrid}>
                  <div style={formGroupStyle}>
                    <label style={labelStyle}>Link to Campaign (Optional)</label>
                    <select 
                      value={selectedCampaignId} 
                      onChange={(e) => setSelectedCampaignId(e.target.value)}
                      style={selectStyle}
                    >
                      <option value="">No Campaign Link</option>
                      {campaigns.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>

                  <div style={formGroupStyle}>
                    <label style={labelStyle}>Schedule Type</label>
                    <select 
                      value={scheduleType} 
                      onChange={(e) => setScheduleType(e.target.value)}
                      style={selectStyle}
                    >
                      <option value="scheduled">Scheduled Publication</option>
                      <option value="draft">Save as Draft</option>
                      <option value="recurring">Recurring Queue</option>
                    </select>
                  </div>

                  {scheduleType === 'recurring' && (
                    <div style={formGroupStyle}>
                      <label style={labelStyle}>Recurrence</label>
                      <select 
                        value={recurrencePattern} 
                        onChange={(e) => setRecurrencePattern(e.target.value)}
                        style={selectStyle}
                      >
                        <option value="daily">Daily Interval</option>
                        <option value="weekly">Weekly Interval</option>
                        <option value="monthly">Monthly Interval</option>
                      </select>
                    </div>
                  )}

                  {scheduleType !== 'draft' && (
                    <div style={formGroupStyle}>
                      <label style={labelStyle}>Publishing Time</label>
                      <input
                        type="datetime-local"
                        value={scheduleTime}
                        onChange={(e) => setScheduleTime(e.target.value)}
                        style={inputStyle}
                      />
                    </div>
                  )}
                </div>

                <button type="submit" className="btn-primary" style={submitFormBtnStyle}>
                  <FiClock /> {scheduleType === 'draft' ? 'Save Draft' : 'Queue Post'}
                </button>
              </form>
            )}
          </div>

          {/* Right Live Preview Panel */}
          {renderLiveMockPreview()}
        </div>
      )}

      {/* TAB CONTENT: QUEUES & DRAFTS MANAGEMENT */}
      {activeTab === 'queue' && (
        <div style={queueLayoutContainer}>
          {/* Queue Filter bar */}
          <div style={queueFilterContainer} className="glass-panel">
            <button 
              type="button" 
              style={queueFilter === 'all' ? activeQueueFilterBtn : queueFilterBtn} 
              onClick={() => setQueueFilter('all')}
            >
              All Posts ({posts.length})
            </button>
            <button 
              type="button" 
              style={queueFilter === 'scheduled' ? activeQueueFilterBtn : queueFilterBtn} 
              onClick={() => setQueueFilter('scheduled')}
            >
              Scheduled ({posts.filter(p => p.status === 'scheduled' && p.schedule_type !== 'draft').length})
            </button>
            <button 
              type="button" 
              style={queueFilter === 'draft' ? activeQueueFilterBtn : queueFilterBtn} 
              onClick={() => setQueueFilter('draft')}
            >
              Drafts ({posts.filter(p => p.schedule_type === 'draft').length})
            </button>
            <button 
              type="button" 
              style={queueFilter === 'published' ? activeQueueFilterBtn : queueFilterBtn} 
              onClick={() => setQueueFilter('published')}
            >
              Published ({posts.filter(p => p.status === 'published').length})
            </button>
            <button 
              type="button" 
              style={queueFilter === 'failed' ? activeQueueFilterBtn : queueFilterBtn} 
              onClick={() => setQueueFilter('failed')}
            >
              Failed ({posts.filter(p => p.status === 'failed').length})
            </button>
          </div>

          {getFilteredPosts().length === 0 ? (
            <div className="glass-panel" style={emptyStateStyle}>
              <FiLayers size={40} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
              <h3>No matching posts found in this queue</h3>
              <p>Try switching filters or create a new post.</p>
            </div>
          ) : (
            <div style={postsListGrid}>
              {getFilteredPosts().map(p => {
                const isFailed = p.status === 'failed';
                const isPublished = p.status === 'published';
                
                return (
                  <div key={p.id} className="glass-panel glass-card-hover" style={postCardStyle}>
                    <div style={postCardHeaderStyle}>
                      <span style={postStatusBadge(p.status)}>
                        {p.status.toUpperCase()}
                      </span>
                      <span style={postTypeTextStyle}>
                        Type: {p.schedule_type.toUpperCase()} 
                        {p.recurrence_pattern ? ` (${p.recurrence_pattern})` : ''}
                      </span>
                    </div>

                    <p style={postBodyContentStyle}>{p.content_text}</p>
                    
                    {p.media_urls && p.media_urls.length > 0 && (
                      <div style={postCardMediaPreviewRow}>
                        {p.media_urls.map((url, idx) => (
                          <span key={idx} style={previewMediaUrlBadge}>
                            {url.startsWith('blob:') ? 'Selected Image' : `Media #${idx + 1}`}
                          </span>
                        ))}
                      </div>
                    )}

                    <div style={postMetaRow}>
                      <div style={postTargetsRow}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Publish Targets: </span>
                        <div style={targetIconsGrid}>
                          {p.platform_targets.map(tarId => {
                            const matchChan = channels.find(c => c.id === tarId);
                            return matchChan ? (
                              <div key={tarId} title={matchChan.account_name} style={miniAvatarIconStyle}>
                                {getPlatformIcon(matchChan.platform)}
                              </div>
                            ) : null;
                          })}
                        </div>
                      </div>
                      
                      {p.scheduled_at && (
                        <span style={scheduledTimeTextStyle}>
                          <FiClock size={12} /> {new Date(p.scheduled_at).toLocaleString()}
                        </span>
                      )}
                    </div>

                    {p.publishing_logs && p.publishing_logs.length > 0 && (
                      <div style={logHistorySectionStyle}>
                        <button 
                          type="button" 
                          onClick={() => setExpandedPostHistoryId(prev => prev === p.id ? null : p.id)}
                          style={toggleLogsBtnStyle}
                        >
                          {expandedPostHistoryId === p.id ? <FiChevronUp /> : <FiChevronDown />} 
                          {expandedPostHistoryId === p.id ? 'Hide Logs' : 'View Publishing History'} ({p.publishing_logs.length})
                        </button>
                        
                        {expandedPostHistoryId === p.id && (
                           <div style={logsDropdownContainer} className="animate-fade-in">
                             {p.publishing_logs.map(log => (
                               <div key={log.id} style={logItemRowStyle}>
                                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                   <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                     {log.status === 'success' ? (
                                       <FiCheckCircle style={{ color: 'var(--success)' }} />
                                     ) : (
                                       <FiAlertCircle style={{ color: 'var(--error)' }} />
                                     )}
                                     <strong style={{ textTransform: 'capitalize' }}>{log.platform}</strong>: {log.status.toUpperCase()}
                                   </span>
                                   <span style={logTimeStyle}>{new Date(log.published_at).toLocaleString()}</span>
                                 </div>
                                 {log.error_message && (
                                   <div style={logErrorTextStyle}>{log.error_message}</div>
                                 )}
                                </div>
                             ))}
                           </div>
                        )}
                      </div>
                    )}

                    <div style={postCardActionsStyle}>
                      {!isPublished && (
                        <button 
                          className="btn-primary" 
                          style={postActionBtnStyle} 
                          onClick={() => handlePublishNow(p.id)}
                        >
                          <FiSend /> Publish Now
                        </button>
                      )}

                      {isFailed && (
                        <button 
                          className="btn-primary" 
                          style={{ ...postActionBtnStyle, background: 'linear-gradient(135deg, var(--warning) 0%, var(--primary) 100%)' }} 
                          onClick={() => handleRetryPost(p.id)}
                        >
                          <FiRefreshCw /> Retry Publishing
                        </button>
                      )}
                      
                      <button 
                        className="btn-danger" 
                        style={postDeleteBtnStyle} 
                        onClick={() => handleDeletePost(p.id)}
                      >
                        <FiTrash2 /> Remove
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: VISUAL CALENDAR */}
      {activeTab === 'calendar' && (
        <div className="glass-panel" style={calendarWrapperCard}>
          <div style={calendarHeaderControls}>
            <button className="btn-secondary" style={calendarControlBtn} onClick={handlePrevMonth}>
              &lt; Prev Month
            </button>
            <h3 style={calendarMonthTitle}>
              {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
            </h3>
            <button className="btn-secondary" style={calendarControlBtn} onClick={handleNextMonth}>
              Next Month &gt;
            </button>
          </div>

          <div style={weekdaysGridStyle}>
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(dayName => (
              <div key={dayName} style={weekdayHeaderCell}>{dayName}</div>
            ))}
          </div>

          <div style={calendarGridStyle}>
            {getDaysInMonth(currentDate).map((day, idx) => {
              if (day === null) {
                return <div key={`spacer-${idx}`} style={calendarEmptyCell}></div>;
              }
              
              const dayPosts = getPostsForDate(day);
              const isToday = new Date().getDate() === day.getDate() && 
                              new Date().getMonth() === day.getMonth() && 
                              new Date().getFullYear() === day.getFullYear();
                              
              return (
                <div 
                  key={day.toISOString()} 
                  style={{ ...calendarDayCell(isToday), cursor: 'pointer', transition: 'all 0.2s' }}
                  onClick={() => openCalendarModal(day)}
                  title={`Click to schedule a post on ${day.toLocaleDateString()}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={dayNumberStyle(isToday)}>{day.getDate()}</span>
                    <button 
                      type="button"
                      style={{ 
                        background: 'rgba(99, 102, 241, 0.12)', 
                        border: 'none', 
                        borderRadius: '4px', 
                        color: 'var(--primary)', 
                        cursor: 'pointer', 
                        padding: '2px 6px',
                        fontSize: '0.7rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '2px'
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        openCalendarModal(day);
                      }}
                      title="Schedule Post"
                    >
                      <FiPlus size={10} /> Add
                    </button>
                  </div>
                  
                  {dayPosts.length > 0 ? (
                    <div style={dayPostsWrapper}>
                      {dayPosts.map(p => (
                        <div 
                          key={p.id} 
                          style={calendarIndicatorBar(p.status)}
                          title={`${p.status.toUpperCase()} - ${p.content_text}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveTab('queue');
                            setQueueFilter('all');
                          }}
                        >
                          <span style={indicatorTextStyle}>{p.content_text.substring(0, 15)}...</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '8px', fontStyle: 'italic', opacity: 0.6 }}>
                      + Click to schedule
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* QUICK ADD CALENDAR MODAL POPUP */}
      {isCalendarModalOpen && (
        <div style={modalOverlayStyle}>
          <div className="glass-panel animate-fade-in" style={modalContentStyle}>
            <div style={modalHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                📅 Schedule Post for {modalDate?.toLocaleDateString('default', { month: 'short', day: 'numeric', year: 'numeric' })}
              </h3>
              <button 
                type="button" 
                onClick={() => setIsCalendarModalOpen(false)} 
                style={modalCloseBtnStyle}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleModalSavePost} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {modalError && (
                <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--error)', borderRadius: '8px', color: 'var(--error)', fontSize: '0.84rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FiAlertCircle size={16} />
                  <span>{modalError}</span>
                </div>
              )}
              <div style={formGroupStyle}>
                <label style={labelStyle}>Content Caption</label>
                <textarea
                  rows={4}
                  value={modalContent}
                  onChange={(e) => setModalContent(e.target.value)}
                  placeholder="Mention anything here for this calendar date... (e.g. 🎉 Special Announcement, Product Launch, Weekly Digest)"
                  style={textareaStyle}
                  required
                  autoFocus
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Publishing Date & Time</label>
                <input
                  type="datetime-local"
                  value={modalScheduleTime}
                  onChange={(e) => setModalScheduleTime(e.target.value)}
                  style={inputStyle}
                  required
                />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Target Channels</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {channels.map(ch => {
                    const isSelected = modalSelectedChannels.includes(ch.id);
                    return (
                      <div
                        key={ch.id}
                        onClick={() => {
                          setModalSelectedChannels(prev => 
                            prev.includes(ch.id) ? prev.filter(id => id !== ch.id) : [...prev, ch.id]
                          );
                        }}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '20px',
                          border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                          background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                          color: isSelected ? 'var(--primary)' : 'var(--text-secondary)',
                          cursor: 'pointer',
                          fontSize: '0.8rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        {getPlatformIcon(ch.platform)} {ch.account_name}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Media URL (Optional)</label>
                <input
                  type="text"
                  value={modalMediaUrl}
                  onChange={(e) => setModalMediaUrl(e.target.value)}
                  placeholder="https://images.unsplash.com/photo-1518770660439-4636190af475"
                  style={inputStyle}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
                <button 
                  type="button" 
                  className="btn-secondary" 
                  onClick={() => setIsCalendarModalOpen(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={modalSubmitting}
                >
                  {modalSubmitting ? 'Scheduling...' : 'Schedule Post on Calendar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DEVICE POST PREVIEW RESPONSIVE MODAL (NO ROUTE CHANGE) */}
      <DevicePreviewModal 
        isOpen={showDevicePreviewModal} 
        onClose={() => setShowDevicePreviewModal(false)}
        content={content}
        mediaUrls={mediaUrls}
        targetPlatforms={selectedChannels}
      />
    </div>
  );
};

// Quick Add Calendar Modal Styles
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
  maxWidth: '520px',
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

const tabMenuRowStyle = {
  display: 'flex',
  gap: '12px',
  marginBottom: '24px',
  borderBottom: '1px solid var(--border-color)',
  paddingBottom: '10px'
};

const subTabStyle = {
  padding: '8px 16px',
  background: 'transparent',
  border: 'none',
  outline: 'none',
  cursor: 'pointer',
  color: 'var(--text-secondary)',
  fontSize: '0.88rem',
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  fontWeight: '500',
  borderRadius: '8px',
  transition: 'all 0.3s'
};

const activeSubTabStyle = {
  ...subTabStyle,
  color: 'var(--primary)',
  background: 'rgba(99, 102, 241, 0.08)'
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

// Split columns layout for Compose & Live Preview
const composeLayoutGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
  gap: '24px',
  alignItems: 'start'
};

const panelContainerStyle = {
  padding: '32px'
};

const formStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '20px'
};

const formGroupStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px'
};

const labelStyle = {
  fontSize: '0.9rem',
  fontWeight: '600',
  color: 'var(--text-secondary)',
  textAlign: 'left'
};

const channelsGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
  gap: '16px'
};

const channelPickerCard = (selected, expired) => ({
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '12px 16px',
  borderRadius: '10px',
  border: selected ? '1.5px solid var(--primary)' : '1px solid var(--border-color)',
  background: selected ? 'rgba(99,102,241,0.03)' : 'rgba(255,255,255,0.01)',
  cursor: expired ? 'not-allowed' : 'pointer',
  opacity: expired ? 0.5 : 1,
  transition: 'all 0.2s ease'
});

const channelAvatarStyle = {
  width: '36px',
  height: '36px',
  borderRadius: '50%'
};

const channelTitleRow = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px'
};

const channelNameStyle = {
  fontSize: '0.85rem',
  fontWeight: '600'
};

const channelStatusText = (expired) => ({
  fontSize: '0.72rem',
  color: expired ? 'var(--error)' : 'var(--text-muted)'
});

const textareaStyle = {
  width: '100%',
  minHeight: '120px',
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  padding: '12px 16px',
  color: 'var(--text-primary)',
  fontSize: '0.92rem',
  outline: 'none',
  fontFamily: 'inherit',
  resize: 'vertical',
  textAlign: 'left'
};

const charCountStyle = {
  fontSize: '0.76rem',
  color: 'var(--text-muted)',
  textAlign: 'right'
};

// Drag and drop style
const dragDropAreaStyle = {
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '24px',
  border: '2px dashed var(--border-color)',
  borderRadius: '10px',
  background: 'rgba(255, 255, 255, 0.005)',
  cursor: 'pointer',
  textAlign: 'center',
  transition: 'border-color 0.2s ease'
};

const dragDropLabel = {
  fontSize: '0.82rem',
  color: 'var(--text-secondary)',
  fontWeight: '500'
};

const mediaInputRow = {
  display: 'flex',
  gap: '12px',
  marginTop: '4px'
};

const inputStyle = {
  flex: 1,
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  padding: '10px 16px',
  color: 'var(--text-primary)',
  fontSize: '0.9rem',
  outline: 'none'
};

const addMediaBtnStyle = {
  padding: '0 20px',
  height: '42px',
  fontSize: '0.85rem'
};

const mediaListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  marginTop: '10px'
};

const mediaItemStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '10px 16px',
  borderRadius: '8px',
  border: '1px solid var(--border-color)',
  background: 'rgba(255,255,255,0.01)'
};

const mediaUrlTextStyle = {
  fontSize: '0.8rem',
  color: 'var(--text-secondary)',
  wordBreak: 'break-all',
  marginRight: '12px'
};

const mediaRemoveBtn = {
  background: 'transparent',
  border: 'none',
  color: 'var(--error)',
  cursor: 'pointer',
  padding: '4px'
};

const schedulingSettingsGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
  gap: '20px'
};

const selectStyle = {
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid var(--border-color)',
  borderRadius: '10px',
  padding: '10px 16px',
  color: 'var(--text-primary)',
  fontSize: '0.9rem',
  outline: 'none',
  cursor: 'pointer'
};

const submitFormBtnStyle = {
  padding: '12px 24px',
  fontSize: '0.9rem',
  alignSelf: 'start',
  marginTop: '8px',
  display: 'flex',
  alignItems: 'center',
  gap: '8px'
};

// Queue Styles
const queueLayoutContainer = {
  width: '100%'
};

const queueFilterContainer = {
  display: 'flex',
  gap: '10px',
  padding: '10px 16px',
  marginBottom: '24px',
  flexWrap: 'wrap'
};

const queueFilterBtn = {
  padding: '8px 16px',
  fontSize: '0.8rem',
  background: 'transparent',
  border: 'none',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  borderRadius: '6px',
  transition: 'all 0.2s'
};

const activeQueueFilterBtn = {
  ...queueFilterBtn,
  color: 'var(--primary)',
  background: 'rgba(99, 102, 241, 0.08)'
};

const postsListGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
  gap: '24px'
};

const postCardStyle = {
  padding: '24px',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
  background: 'rgba(255, 255, 255, 0.01)'
};

const postCardHeaderStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center'
};

const postStatusBadge = (status) => {
  let color = 'var(--text-secondary)';
  let bg = 'rgba(255,255,255,0.05)';
  if (status === 'published') { color = 'var(--success)'; bg = 'rgba(16, 185, 129, 0.1)'; }
  else if (status === 'failed') { color = 'var(--error)'; bg = 'rgba(244, 63, 94, 0.1)'; }
  else if (status === 'scheduled') { color = 'var(--warning)'; bg = 'rgba(245, 158, 11, 0.1)'; }
  
  return {
    fontSize: '0.72rem',
    fontWeight: '600',
    color: color,
    background: bg,
    padding: '3px 8px',
    borderRadius: '10px'
  };
};

const postTypeTextStyle = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)',
  fontWeight: '500'
};

const postBodyContentStyle = {
  fontSize: '0.92rem',
  lineHeight: '1.5',
  color: 'var(--text-primary)',
  wordBreak: 'break-word',
  textAlign: 'left'
};

const postCardMediaPreviewRow = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '6px'
};

const previewMediaUrlBadge = {
  fontSize: '0.74rem',
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid var(--border-color)',
  padding: '2px 6px',
  borderRadius: '4px',
  color: 'var(--text-secondary)'
};

const postMetaRow = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  borderTop: '1px solid var(--border-color)',
  paddingTop: '12px',
  marginTop: '4px'
};

const postTargetsRow = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px'
};

const targetIconsGrid = {
  display: 'flex',
  gap: '4px'
};

const miniAvatarIconStyle = {
  padding: '4px',
  background: 'rgba(255,255,255,0.03)',
  borderRadius: '50%',
  border: '1px solid var(--border-color)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '0.75rem'
};

const scheduledTimeTextStyle = {
  fontSize: '0.76rem',
  color: 'var(--text-secondary)',
  display: 'flex',
  alignItems: 'center',
  gap: '6px'
};

const logHistorySectionStyle = {
  marginTop: '12px',
  borderTop: '1px solid rgba(255,255,255,0.05)',
  paddingTop: '12px',
  textAlign: 'left'
};

const toggleLogsBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-secondary)',
  fontSize: '0.8rem',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  padding: '4px 0',
  outline: 'none'
};

const logsDropdownContainer = {
  marginTop: '8px',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  background: 'rgba(0,0,0,0.2)',
  padding: '12px',
  borderRadius: '8px',
  maxHeight: '160px',
  overflowY: 'auto'
};

const logItemRowStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '2px',
  fontSize: '0.78rem',
  color: 'var(--text-secondary)',
  borderBottom: '1px solid rgba(255,255,255,0.03)',
  paddingBottom: '6px'
};

const logTimeStyle = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)'
};

const logErrorTextStyle = {
  fontSize: '0.72rem',
  color: 'var(--error)',
  background: 'rgba(244,63,94,0.05)',
  padding: '4px 8px',
  borderRadius: '4px',
  marginTop: '2px',
  fontStyle: 'italic',
  textAlign: 'left'
};

const postCardActionsStyle = {
  display: 'flex',
  gap: '12px',
  marginTop: '8px'
};

const postActionBtnStyle = {
  flex: 1,
  padding: '8px 16px',
  fontSize: '0.8rem',
  height: '34px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '6px'
};

const postDeleteBtnStyle = {
  ...postActionBtnStyle,
  flex: 0,
  padding: '0 12px'
};

// Calendar Layout Styles
const calendarWrapperCard = {
  padding: '32px'
};

const calendarHeaderControls = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '24px'
};

const calendarControlBtn = {
  padding: '8px 16px',
  fontSize: '0.82rem'
};

const calendarMonthTitle = {
  fontSize: '1.25rem',
  fontWeight: '600'
};

const weekdaysGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(7, 1fr)',
  gap: '8px',
  marginBottom: '8px',
  textAlign: 'center'
};

const weekdayHeaderCell = {
  fontSize: '0.8rem',
  fontWeight: '600',
  color: 'var(--text-secondary)',
  padding: '6px 0'
};

const calendarGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(7, 1fr)',
  gap: '8px',
  gridAutoRows: 'minmax(90px, auto)'
};

const calendarEmptyCell = {
  background: 'transparent',
  border: 'none'
};

const calendarDayCell = (today) => ({
  background: today ? 'rgba(99, 102, 241, 0.03)' : 'rgba(255, 255, 255, 0.01)',
  border: today ? '1px solid var(--primary)' : '1px solid var(--border-color)',
  borderRadius: '8px',
  padding: '10px',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  position: 'relative'
});

const dayNumberStyle = (today) => ({
  fontSize: '0.85rem',
  fontWeight: today ? '700' : '500',
  color: today ? 'var(--primary)' : 'var(--text-secondary)',
  alignSelf: 'start'
});

const dayPostsWrapper = {
  display: 'flex',
  flexDirection: 'column',
  gap: '4px',
  width: '100%',
  overflow: 'hidden'
};

const calendarIndicatorBar = (status) => {
  let bg = 'rgba(255,255,255,0.05)';
  let border = '1px solid var(--border-color)';
  if (status === 'published') { bg = 'rgba(16, 185, 129, 0.15)'; border = '1px solid rgba(16, 185, 129, 0.3)'; }
  else if (status === 'failed') { bg = 'rgba(244, 63, 94, 0.15)'; border = '1px solid rgba(244, 63, 94, 0.3)'; }
  else if (status === 'scheduled') { bg = 'rgba(245, 158, 11, 0.15)'; border = '1px solid rgba(245, 158, 11, 0.3)'; }
  
  return {
    padding: '3px 6px',
    borderRadius: '4px',
    background: bg,
    border: border,
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    width: '100%'
  };
};

const indicatorTextStyle = {
  fontSize: '0.68rem',
  color: 'var(--text-primary)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: 'block',
  width: '100%'
};

const emptyChannelsStyle = {
  padding: '40px 20px',
  textAlign: 'center',
  color: 'var(--text-muted)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
};

const emptyStateStyle = {
  padding: '64px 32px',
  textAlign: 'center',
  color: 'var(--text-muted)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
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

// Social media live preview mock stylings
const previewContainerStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px'
};

const previewTitleStyle = {
  fontSize: '1.15rem',
  fontWeight: '600',
  textAlign: 'left'
};

const platformTabsStyle = {
  display: 'flex',
  gap: '8px',
  borderBottom: '1px solid var(--border-color)',
  paddingBottom: '8px'
};

const platformTabStyle = {
  padding: '6px 12px',
  background: 'transparent',
  border: 'none',
  color: 'var(--text-secondary)',
  fontSize: '0.8rem',
  cursor: 'pointer',
  borderRadius: '4px',
  transition: 'all 0.2s'
};

const activePlatformTabStyle = {
  ...platformTabStyle,
  color: 'var(--primary)',
  background: 'rgba(99, 102, 241, 0.06)'
};

const mockPostCardStyle = {
  background: 'rgba(255, 255, 255, 0.01)',
  border: '1px solid var(--border-color)',
  borderRadius: '12px',
  padding: '20px',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px'
};

const mockPostHeader = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px'
};

const mockPostAvatar = {
  width: '38px',
  height: '38px',
  borderRadius: '50%',
  background: 'rgba(255,255,255,0.05)'
};

const mockPostUserRow = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-start'
};

const mockPostName = {
  fontSize: '0.88rem',
  fontWeight: '600',
  color: 'var(--text-primary)'
};

const mockPostMeta = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)'
};

const mockPostContent = {
  fontSize: '0.88rem',
  lineHeight: '1.45',
  color: 'var(--text-secondary)',
  textAlign: 'left',
  wordBreak: 'break-word',
  whiteSpace: 'pre-wrap'
};

const mockPostImageContainer = {
  width: '100%',
  borderRadius: '8px',
  overflow: 'hidden',
  border: '1px solid var(--border-color)',
  background: 'rgba(0,0,0,0.15)'
};

const mockPostImage = {
  width: '100%',
  height: 'auto',
  maxHeight: '260px',
  objectFit: 'cover'
};

const mockPostActions = {
  display: 'flex',
  justifyContent: 'space-between',
  borderTop: '1px solid var(--border-color)',
  paddingTop: '12px',
  marginTop: '4px'
};

const mockPostActionItem = {
  fontSize: '0.78rem',
  color: 'var(--text-secondary)',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  cursor: 'pointer'
};

export default Scheduler;

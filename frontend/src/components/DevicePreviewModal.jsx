import React, { useState } from 'react';
import { 
  FiSmartphone, FiTablet, FiMonitor, FiX, FiThumbsUp, 
  FiMessageSquare, FiShare2, FiHeart, FiRepeat, FiSend, 
  FiCheckCircle, FiMoreHorizontal, FiGlobe, FiLayers
} from 'react-icons/fi';
import { FaLinkedinIn, FaFacebookF, FaInstagram, FaTwitter, FaYoutube } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

export const DevicePreviewModal = ({ 
  isOpen, 
  onClose, 
  content = '', 
  mediaUrls = [], 
  targetPlatforms = ['linkedin', 'facebook', 'instagram', 'twitter', 'youtube'] 
}) => {
  const { user } = useAuth();
  const [deviceMode, setDeviceMode] = useState('mobile'); // mobile, tablet, desktop
  const [selectedPlatform, setSelectedPlatform] = useState('linkedin'); // linkedin, facebook, instagram, twitter, youtube
  const [selectedDemoIndex, setSelectedDemoIndex] = useState(0);

  if (!isOpen) return null;

  // Rich Demo Post Dataset
  const demoPosts = [
    {
      id: "demo_1",
      title: "🚀 Product Launch Announcement",
      caption: "🚀 SocialPilot 2.0 Feature Release: Multi-Channel Publishing, Automated Calendars & Real-Time Analytics! Scale your social reach effortlesly. #SocialPilot #SaaS #Marketing",
      mediaUrl: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1000&auto=format&fit=crop&q=80",
      likes: "14,200",
      comments: "1,850",
      shares: "2,100",
      views: "84.5K"
    },
    {
      id: "demo_2",
      title: "💡 SaaS Growth Strategy Breakdown",
      caption: "💡 5 Proven Social Media Growth Strategies for Enterprise SaaS Teams. Boost organic reach by 300% with structured content pillars & automated scheduling! #GrowthHacks #B2B",
      mediaUrl: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1000&auto=format&fit=crop&q=80",
      likes: "12,800",
      comments: "1,420",
      shares: "1,650",
      views: "72.4K"
    },
    {
      id: "demo_3",
      title: "🎉 Live Q&A & Webinar Stream",
      caption: "🎉 Live Q&A Stream: Scaling Brand Awareness & Lead Generation across Meta, LinkedIn & YouTube. Join our lead growth architects this Thursday at 10 AM EST!",
      mediaUrl: "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=1000&auto=format&fit=crop&q=80",
      likes: "9,400",
      comments: "1,180",
      shares: "1,100",
      views: "48.2K"
    },
    {
      id: "demo_4",
      title: "🔥 Creator Case Study & Spotlight",
      caption: "🔥 Creator Spotlight: How Apex Marketing Agency Automated 80% of Client Publishing Workflows using SocialPilot's Visual Calendar. Read the full case study!",
      mediaUrl: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1000&auto=format&fit=crop&q=80",
      likes: "18,500",
      comments: "2,140",
      shares: "2,650",
      views: "96.2K"
    },
    {
      id: "demo_5",
      title: "📈 Q3 Industry Benchmark Report",
      caption: "📈 Q3 Industry Benchmark Report: Social Media ROI, Conversion Funnels & Audience Growth Trends. Download the free 30-page PDF report now!",
      mediaUrl: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1000&auto=format&fit=crop&q=80",
      likes: "6,200",
      comments: "680",
      shares: "890",
      views: "34.8K"
    }
  ];

  const activeDemo = demoPosts[selectedDemoIndex];
  const profileName = user?.name || user?.full_name || 'Enterprise Publisher';
  const profilePic = `https://api.dicebear.com/7.x/initials/svg?seed=${profileName}`;
  
  const displayCaption = content && content.trim().length > 0 ? content : activeDemo.caption;
  const displayMedia = Array.isArray(mediaUrls) && mediaUrls.length > 0 ? mediaUrls[0] : activeDemo.mediaUrl;

  // Device Container Widths
  const getDeviceWidth = () => {
    switch (deviceMode) {
      case 'mobile': return '375px';
      case 'tablet': return '680px';
      case 'desktop': return '850px';
      default: return '375px';
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(10px)',
      zIndex: 99999,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      {/* Modal Toolbar Header */}
      <div style={{
        width: '100%',
        maxWidth: '920px',
        background: 'var(--card-bg, #181825)',
        border: '1px solid var(--border-color)',
        borderRadius: '16px 16px 0 0',
        padding: '16px 24px',
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📱 Device Post Live Preview
          </h3>
          <span style={{ fontSize: '0.75rem', padding: '3px 8px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.2)', color: 'var(--primary)', fontWeight: 'bold' }}>
            Interactive Demo
          </span>
        </div>

        {/* Demo Post Selection Selector Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FiLayers style={{ color: 'var(--primary)' }} />
          <select
            value={selectedDemoIndex}
            onChange={(e) => setSelectedDemoIndex(Number(e.target.value))}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'rgba(0,0,0,0.4)',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            {demoPosts.map((dp, idx) => (
              <option key={dp.id} value={idx}>{dp.title}</option>
            ))}
          </select>
        </div>

        {/* Viewport Device Mode Selector */}
        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
          <button
            type="button"
            onClick={() => setDeviceMode('mobile')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              border: 'none',
              background: deviceMode === 'mobile' ? 'var(--primary)' : 'transparent',
              color: deviceMode === 'mobile' ? '#fff' : 'var(--text-muted)',
              fontSize: '0.8rem',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            <FiSmartphone size={14} /> Mobile
          </button>
          <button
            type="button"
            onClick={() => setDeviceMode('tablet')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              border: 'none',
              background: deviceMode === 'tablet' ? 'var(--primary)' : 'transparent',
              color: deviceMode === 'tablet' ? '#fff' : 'var(--text-muted)',
              fontSize: '0.8rem',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            <FiTablet size={14} /> Tablet
          </button>
          <button
            type="button"
            onClick={() => setDeviceMode('desktop')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              border: 'none',
              background: deviceMode === 'desktop' ? 'var(--primary)' : 'transparent',
              color: deviceMode === 'desktop' ? '#fff' : 'var(--text-muted)',
              fontSize: '0.8rem',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            <FiMonitor size={14} /> Desktop
          </button>
        </div>

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: 'none',
            color: 'var(--text-primary)',
            width: '34px',
            height: '34px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '1.1rem'
          }}
        >
          <FiX />
        </button>
      </div>

      {/* Modal Main Body */}
      <div style={{
        width: '100%',
        maxWidth: '920px',
        height: '620px',
        maxHeight: '75vh',
        background: '#0d0e15',
        border: '1px solid var(--border-color)',
        borderTop: 'none',
        borderRadius: '0 0 16px 16px',
        padding: '24px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>

        {/* Social Channel Selector Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {[
            { id: 'linkedin', name: 'LinkedIn', icon: <FaLinkedinIn style={{ color: '#0a66c2' }} /> },
            { id: 'facebook', name: 'Facebook', icon: <FaFacebookF style={{ color: '#1877f2' }} /> },
            { id: 'instagram', name: 'Instagram', icon: <FaInstagram style={{ color: '#e1306c' }} /> },
            { id: 'twitter', name: 'X / Twitter', icon: <FaTwitter style={{ color: '#1da1f2' }} /> },
            { id: 'youtube', name: 'YouTube', icon: <FaYoutube style={{ color: '#ff0000' }} /> }
          ].map(p => {
            const isSel = selectedPlatform === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelectedPlatform(p.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '20px',
                  border: isSel ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                  background: isSel ? 'rgba(99, 102, 241, 0.18)' : 'rgba(255,255,255,0.03)',
                  color: isSel ? '#fff' : 'var(--text-secondary)',
                  fontSize: '0.84rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                {p.icon} {p.name}
              </button>
            );
          })}
        </div>

        {/* DEVICE SIMULATOR FRAME */}
        <div style={{
          width: getDeviceWidth(),
          transition: 'all 0.3s ease-in-out',
          background: selectedPlatform === 'instagram' || selectedPlatform === 'twitter' ? '#000000' : '#1b1f2b',
          borderRadius: deviceMode === 'mobile' ? '32px' : '16px',
          border: deviceMode === 'mobile' ? '12px solid #2a2e3d' : '4px solid #2a2e3d',
          padding: deviceMode === 'mobile' ? '20px 16px' : '20px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          textAlign: 'left',
          color: '#ffffff'
        }}>
          {/* Mobile Notch Indicator */}
          {deviceMode === 'mobile' && (
            <div style={{ width: '120px', height: '14px', background: '#2a2e3d', borderRadius: '0 0 10px 10px', margin: '-20px auto 16px auto' }}></div>
          )}

          {/* 1. LINKEDIN PREVIEW MOCK */}
          {selectedPlatform === 'linkedin' && (
            <div>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <img src={profilePic} alt="User" style={{ width: '46px', height: '46px', borderRadius: '50%' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: '700', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {profileName} <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>• 1st</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Enterprise Growth Specialist @ SocialPilot</div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Just now • <FiGlobe size={11} />
                  </div>
                </div>
                <FiMoreHorizontal style={{ color: '#94a3b8' }} />
              </div>

              <div style={{ fontSize: '0.88rem', lineHeight: '1.5', color: '#e2e8f0', marginBottom: '12px', whiteSpace: 'pre-wrap' }}>
                {displayCaption}
              </div>

              {displayMedia && (
                <div style={{ borderRadius: '8px', overflow: 'hidden', marginBottom: '12px', maxHeight: '340px' }}>
                  <img src={displayMedia} alt="Post asset" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: '#94a3b8', borderBottom: '1px solid #334155', paddingBottom: '8px', marginBottom: '10px' }}>
                <span>👍 {activeDemo.likes} • {activeDemo.comments} comments</span>
                <span>{activeDemo.shares} shares</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-around', color: '#94a3b8', fontSize: '0.82rem', fontWeight: '600' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}><FiThumbsUp /> Like</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}><FiMessageSquare /> Comment</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}><FiShare2 /> Repost</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}><FiSend /> Send</span>
              </div>
            </div>
          )}

          {/* 2. FACEBOOK PREVIEW MOCK */}
          {selectedPlatform === 'facebook' && (
            <div>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <img src={profilePic} alt="User" style={{ width: '42px', height: '42px', borderRadius: '50%' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: '700', color: '#fff' }}>{profileName}</div>
                  <div style={{ fontSize: '0.74rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Just now • 🌐 Facebook Page
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.88rem', lineHeight: '1.5', color: '#e2e8f0', marginBottom: '12px' }}>
                {displayCaption}
              </div>

              {displayMedia && (
                <div style={{ borderRadius: '8px', overflow: 'hidden', marginBottom: '12px', maxHeight: '340px' }}>
                  <img src={displayMedia} alt="Post asset" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-around', color: '#94a3b8', fontSize: '0.82rem', borderTop: '1px solid #334155', paddingTop: '10px' }}>
                <span>👍 Like ({activeDemo.likes})</span>
                <span>💬 Comment ({activeDemo.comments})</span>
                <span>↗️ Share ({activeDemo.shares})</span>
              </div>
            </div>
          )}

          {/* 3. INSTAGRAM PREVIEW MOCK */}
          {selectedPlatform === 'instagram' && (
            <div>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px' }}>
                <img src={profilePic} alt="User" style={{ width: '36px', height: '36px', borderRadius: '50%', border: '2px solid #e1306c' }} />
                <strong style={{ fontSize: '0.88rem', color: '#fff', flex: 1 }}>{profileName.toLowerCase().replace(/\s+/g, '_')}</strong>
                <FiMoreHorizontal style={{ color: '#fff' }} />
              </div>

              {displayMedia && (
                <div style={{ borderRadius: '10px', overflow: 'hidden', marginBottom: '10px', height: '280px' }}>
                  <img src={displayMedia} alt="Post asset" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '1.2rem' }}>
                <div style={{ display: 'flex', gap: '14px' }}>
                  <FiHeart style={{ color: '#e1306c' }} />
                  <FiMessageSquare />
                  <FiSend />
                </div>
              </div>

              <div style={{ fontSize: '0.82rem', fontWeight: '700', marginBottom: '4px' }}>{activeDemo.likes} likes</div>
              <div style={{ fontSize: '0.82rem', lineHeight: '1.4', color: '#f1f5f9' }}>
                <strong>{profileName.toLowerCase().replace(/\s+/g, '_')}</strong> {displayCaption}
              </div>
            </div>
          )}

          {/* 4. TWITTER / X PREVIEW MOCK */}
          {selectedPlatform === 'twitter' && (
            <div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <img src={profilePic} alt="User" style={{ width: '42px', height: '42px', borderRadius: '50%' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '0.88rem' }}>
                    <strong style={{ color: '#fff' }}>{profileName}</strong>
                    <span style={{ color: '#64748b' }}>@{profileName.toLowerCase().replace(/\s+/g, '')} • 1m</span>
                  </div>
                  <div style={{ fontSize: '0.88rem', lineHeight: '1.4', color: '#e2e8f0', marginTop: '6px' }}>
                    {displayCaption}
                  </div>
                  {displayMedia && (
                    <div style={{ borderRadius: '12px', overflow: 'hidden', marginTop: '10px', maxHeight: '260px' }}>
                      <img src={displayMedia} alt="Post asset" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.8rem', marginTop: '12px' }}>
                    <span>💬 {activeDemo.comments}</span>
                    <span>🔁 {activeDemo.shares}</span>
                    <span>❤️ {activeDemo.likes}</span>
                    <span>📊 {activeDemo.views}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 5. YOUTUBE PREVIEW MOCK */}
          {selectedPlatform === 'youtube' && (
            <div>
              {displayMedia && (
                <div style={{ borderRadius: '12px', overflow: 'hidden', height: '220px', marginBottom: '10px', position: 'relative' }}>
                  <img src={displayMedia} alt="Video thumbnail" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <div style={{ position: 'absolute', bottom: '10px', right: '10px', background: 'rgba(0,0,0,0.8)', color: '#fff', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px' }}>12:45</div>
                </div>
              )}
              <div style={{ display: 'flex', gap: '10px' }}>
                <img src={profilePic} alt="User" style={{ width: '36px', height: '36px', borderRadius: '50%' }} />
                <div>
                  <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#fff' }}>{displayCaption.slice(0, 70)}...</h4>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>{profileName} • {activeDemo.views} views • 2 hours ago</div>
                </div>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};

export default DevicePreviewModal;

import React, { useState } from 'react';
import { 
  FiUsers, FiPlus, FiBriefcase, FiDollarSign, FiGlobe, 
  FiMail, FiCheckCircle, FiClock, FiLink, FiExternalLink, FiBarChart2, FiEdit3, FiTrash2 
} from 'react-icons/fi';
import { FaFacebookF, FaInstagram, FaLinkedinIn, FaTwitter, FaYoutube } from 'react-icons/fa';

const DEFAULT_CLIENTS = [
  {
    id: 'cli_101',
    name: 'Acme Enterprise Technologies',
    industry: 'Enterprise Software & Cloud',
    monthlyBudget: '$15,000 / mo',
    status: 'Active Retainer',
    accountManager: 'Elena Rostova (Marketing Lead)',
    contactEmail: 'marketing@acmetech.io',
    connectedChannels: ['facebook', 'linkedin', 'twitter'],
    activeCampaignsCount: 2,
    impressions: '450.2k',
    roi: '420%'
  },
  {
    id: 'cli_102',
    name: 'TechFlow SaaS Solutions',
    industry: 'Developer Tools & Productivity',
    monthlyBudget: '$12,500 / mo',
    status: 'Active Retainer',
    accountManager: 'David Miller (Performance Lead)',
    contactEmail: 'growth@techflow.dev',
    connectedChannels: ['instagram', 'linkedin', 'youtube'],
    activeCampaignsCount: 3,
    impressions: '620.8k',
    roi: '480%'
  },
  {
    id: 'cli_103',
    name: 'Nexus Health Systems',
    industry: 'Healthcare Technology',
    monthlyBudget: '$18,000 / mo',
    status: 'Quarterly Review',
    accountManager: 'Sarah Jenkins (Business Mgr)',
    contactEmail: 'contact@nexushealth.org',
    connectedChannels: ['facebook', 'linkedin'],
    activeCampaignsCount: 1,
    impressions: '280.4k',
    roi: '390%'
  },
  {
    id: 'cli_104',
    name: 'Apex Global Logistics',
    industry: 'Supply Chain & Logistics',
    monthlyBudget: '$9,500 / mo',
    status: 'Active Retainer',
    accountManager: 'Elena Rostova (Marketing Lead)',
    contactEmail: 'press@apexglobal.com',
    connectedChannels: ['linkedin', 'twitter'],
    activeCampaignsCount: 2,
    impressions: '195.6k',
    roi: '360%'
  }
];

const Clients = () => {
  const [clients, setClients] = useState(DEFAULT_CLIENTS);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  
  // New Client Form
  const [newClientName, setNewClientName] = useState('');
  const [newIndustry, setNewIndustry] = useState('');
  const [newBudget, setNewBudget] = useState('$10,000 / mo');
  const [newEmail, setNewEmail] = useState('');

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'facebook': return <FaFacebookF key={platform} style={{ color: '#1877f2' }} />;
      case 'instagram': return <FaInstagram key={platform} style={{ color: '#e1306c' }} />;
      case 'linkedin': return <FaLinkedinIn key={platform} style={{ color: '#0077b5' }} />;
      case 'twitter': return <FaTwitter key={platform} style={{ color: '#1da1f2' }} />;
      case 'youtube': return <FaYoutube key={platform} style={{ color: '#ff0000' }} />;
      default: return <FiGlobe key={platform} />;
    }
  };

  const handleAddClient = (e) => {
    e.preventDefault();
    if (!newClientName.trim()) return;
    const created = {
      id: `cli_${Date.now()}`,
      name: newClientName.trim(),
      industry: newIndustry.trim() || 'Digital Services',
      monthlyBudget: newBudget.trim() || '$10,000 / mo',
      status: 'Active Retainer',
      accountManager: 'Elena Rostova (Marketing Lead)',
      contactEmail: newEmail.trim() || 'contact@client.com',
      connectedChannels: ['linkedin', 'facebook', 'instagram'],
      activeCampaignsCount: 1,
      impressions: '100.0k',
      roi: '350%'
    };
    setClients(prev => [created, ...prev]);
    setShowAddModal(false);
    setNewClientName('');
    setNewIndustry('');
    setNewEmail('');
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ textAlign: 'left' }}>
          <h2 style={{ fontSize: '1.6rem', margin: '0 0 4px 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FiBriefcase style={{ color: 'var(--primary)' }} /> Client Portfolio Management
          </h2>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Manage corporate client accounts, monthly retainer budgets, campaign assignments, and brand channels.
          </p>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => setShowAddModal(true)} 
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px' }}
        >
          <FiPlus /> Add New Client Account
        </button>
      </div>

      {/* Overview Metric Summary Scorecards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderRadius: '12px' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Total Active Clients</span>
          <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--primary)', marginTop: '4px' }}>{clients.length} Corporate Accounts</div>
        </div>
        <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderRadius: '12px' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Total Monthly Retainer Volume</span>
          <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--success)', marginTop: '4px' }}>$55,000 / mo</div>
        </div>
        <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderRadius: '12px' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Managed Brand Channels</span>
          <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--warning)', marginTop: '4px' }}>12 Social Profiles</div>
        </div>
        <div className="glass-panel" style={{ padding: '20px', textAlign: 'left', borderRadius: '12px' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Average Campaign ROI</span>
          <div style={{ fontSize: '1.6rem', fontWeight: '700', color: '#ec4899', marginTop: '4px' }}>412.5%</div>
        </div>
      </div>

      {/* Clients Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
        {clients.map(cli => (
          <div key={cli.id} className="glass-panel glass-card-hover" style={{ padding: '24px', textAlign: 'left', borderRadius: '14px', position: 'relative' }}>
            
            {/* Header info */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>{cli.name}</h3>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{cli.industry}</span>
              </div>
              <span style={{ 
                fontSize: '0.72rem', 
                background: cli.status === 'Active Retainer' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                color: cli.status === 'Active Retainer' ? 'var(--success)' : 'var(--warning)',
                padding: '4px 10px',
                borderRadius: '12px',
                fontWeight: '600'
              }}>
                {cli.status}
              </span>
            </div>

            {/* Details Grid */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiDollarSign style={{ color: 'var(--success)' }} />
                <span>Monthly Retainer: <strong style={{ color: 'var(--text-primary)' }}>{cli.monthlyBudget}</strong></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiMail style={{ color: 'var(--primary)' }} />
                <span>Contact Email: <strong>{cli.contactEmail}</strong></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiUsers style={{ color: 'var(--warning)' }} />
                <span>Lead Manager: <strong>{cli.accountManager}</strong></span>
              </div>
            </div>

            {/* Connected Brand Channels Row */}
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 14px', borderRadius: '10px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Connected Brand Profiles</span>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '1.2rem' }}>
                {cli.connectedChannels.map(ch => getPlatformIcon(ch))}
              </div>
            </div>

            {/* Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(99, 102, 241, 0.08)', padding: '8px 12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Total Impressions</span>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--primary)' }}>{cli.impressions}</div>
              </div>
              <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '8px 12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Client Campaign ROI</span>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--success)' }}>{cli.roi}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                className="btn-secondary" 
                onClick={() => setSelectedClient(cli)} 
                style={{ flex: 1, height: '36px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
              >
                <FiBarChart2 /> View Client Details
              </button>
            </div>

          </div>
        ))}
      </div>

      {/* Add Client Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-panel" style={{ width: '90%', maxWidth: '500px', padding: '32px', textAlign: 'left', borderRadius: '16px' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '1.3rem', color: 'var(--text-primary)' }}>+ Add New Client Account</h3>
            <form onSubmit={handleAddClient} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>Client Brand Name</label>
                <input 
                  type="text" 
                  required 
                  placeholder="e.g. Acme Corporation" 
                  value={newClientName} 
                  onChange={e => setNewClientName(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--input-bg)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>Industry Vertical</label>
                <input 
                  type="text" 
                  placeholder="e.g. FinTech / SaaS / Retail" 
                  value={newIndustry} 
                  onChange={e => setNewIndustry(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--input-bg)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>Monthly Retainer Budget</label>
                <input 
                  type="text" 
                  placeholder="$12,000 / mo" 
                  value={newBudget} 
                  onChange={e => setNewBudget(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--input-bg)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>Primary Contact Email</label>
                <input 
                  type="email" 
                  placeholder="contact@clientbrand.com" 
                  value={newEmail} 
                  onChange={e => setNewEmail(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--input-bg)', color: 'var(--text-primary)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Save Client Account</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Client Details Modal */}
      {selectedClient && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-panel" style={{ width: '90%', maxWidth: '600px', padding: '32px', textAlign: 'left', borderRadius: '16px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '1.3rem', color: 'var(--primary)' }}>{selectedClient.name} - Executive Brief</h3>
              <button className="btn-secondary" onClick={() => setSelectedClient(null)} style={{ padding: '4px 12px' }}>Close ✕</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px', background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '10px' }}>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Industry</span>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)' }}>{selectedClient.industry}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Monthly Retainer</span>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--success)' }}>{selectedClient.monthlyBudget}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Lead Account Manager</span>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)' }}>{selectedClient.accountManager}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Contact Email</span>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)' }}>{selectedClient.contactEmail}</div>
              </div>
            </div>

            <h4 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '10px' }}>Active Client Marketing Campaigns</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              <div style={{ padding: '12px', background: 'rgba(99, 102, 241, 0.08)', borderRadius: '8px', borderLeft: '3px solid var(--primary)' }}>
                <div style={{ fontSize: '0.88rem', fontWeight: '600', color: 'var(--text-primary)' }}>Q3 Enterprise SaaS Launch</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Facebook & LinkedIn • Target Impressions: 500,000</div>
              </div>
              <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '8px', borderLeft: '3px solid var(--success)' }}>
                <div style={{ fontSize: '0.88rem', fontWeight: '600', color: 'var(--text-primary)' }}>Summer Growth & Engagement Drive</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Instagram & Twitter • Target Impressions: 250,000</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn-primary" onClick={() => setSelectedClient(null)}>Done / Close</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Clients;

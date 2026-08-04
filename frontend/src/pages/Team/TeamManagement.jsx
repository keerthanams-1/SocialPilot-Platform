import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { 
  FiUsers, FiPlus, FiTrash2, FiMail, 
  FiAlertCircle, FiCheckCircle, FiShield, FiUserPlus 
} from 'react-icons/fi';

const TeamManagement = () => {
  const { user } = useAuth();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Create team state
  const [teamName, setTeamName] = useState('');
  const [createError, setCreateError] = useState('');
  const [createSubmitting, setCreateSubmitting] = useState(false);

  // Invite member state
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Marketing Team');
  const [inviteError, setInviteError] = useState('');
  const [inviteSuccess, setInviteSuccess] = useState('');
  const [inviteSubmitting, setInviteSubmitting] = useState(false);

  // General error/success states
  const [actionError, setActionError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

  // Search/fetch team on load
  const loadUserTeam = async () => {
    setLoading(true);
    try {
      const savedTeamId = localStorage.getItem('socialpilot_active_team_id');
      const response = await api.get('/teams/my-teams');
      const rawData = response.data;
      const myTeams = Array.isArray(rawData) ? rawData : (rawData?.data?.teams || rawData?.data || []);
      
      if (Array.isArray(myTeams) && myTeams.length > 0) {
        let teamToLoad = myTeams[0];
        if (savedTeamId) {
          const matched = myTeams.find(t => t.id === savedTeamId);
          if (matched) teamToLoad = matched;
        }
        
        const detailsResponse = await api.get(`/teams/${teamToLoad.id}`);
        let currentTeam = detailsResponse.data;
        
        // Fetch full workspace members and pending invitations from /workspace/members
        try {
          const membersRes = await api.get(`/workspace/members?team_id=${teamToLoad.id}`);
          const fetchedMembers = membersRes.data?.data?.members || (Array.isArray(membersRes.data) ? membersRes.data : []);
          currentTeam = {
            ...currentTeam,
            members: fetchedMembers
          };
        } catch (mErr) {
          console.error("Failed to fetch workspace members", mErr);
        }

        setTeam(currentTeam);
        localStorage.setItem('socialpilot_active_team_id', teamToLoad.id);
      } else {
        setTeam(null);
        localStorage.removeItem('socialpilot_active_team_id');
      }
    } catch (err) {
      console.error("Error loading team", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUserTeam();
  }, []);

  const handleCreateTeam = async (e) => {
    e.preventDefault();
    setCreateError('');
    
    if (!teamName) {
      setCreateError('Team name cannot be blank');
      return;
    }

    setCreateSubmitting(true);
    try {
      const response = await api.post('/teams', { name: teamName });
      const newTeam = response.data;
      
      const populatedMembers = [
        {
          id: user.id,
          user_id: user.id,
          name: user.name || user.full_name,
          email: user.email,
          role: 'owner',
          status: 'active',
          joined_at: new Date().toISOString()
        }
      ];
      
      const populatedTeam = {
        ...newTeam,
        members: populatedMembers
      };
      
      setTeam(populatedTeam);
      localStorage.setItem('socialpilot_active_team_id', newTeam.id);
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Failed to create team workspace');
    } finally {
      setCreateSubmitting(false);
    }
  };

  const handleInviteMember = async (e) => {
    e.preventDefault();
    setInviteError('');
    setInviteSuccess('');

    if (!inviteEmail) {
      setInviteError('Please enter an email address');
      return;
    }

    setInviteSubmitting(true);
    try {
      const response = await api.post('/workspace/invite', {
        team_id: team.id,
        email: inviteEmail,
        role_name: inviteRole
      });
      
      const msg = response.data?.message || `Invitation Sent Successfully!`;
      setInviteSuccess(msg);
      await loadUserTeam();
      setInviteEmail('');
    } catch (err) {
      setInviteError(err.response?.data?.detail || err.response?.data?.message || 'Failed to invite team member');
    } finally {
      setInviteSubmitting(false);
    }
  };

  const handleRemoveMember = async (memberId, memberName) => {
    if (!window.confirm(`Are you sure you want to remove ${memberName || 'this user'} from this team workspace?`)) {
      return;
    }

    setActionError('');
    setActionSuccess('');

    try {
      await api.delete(`/workspace/member/${memberId}?team_id=${team.id}`);
      setActionSuccess(`Removed ${memberName || 'member'} from workspace.`);
      await loadUserTeam();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  const isOwner = team?.owner_id === user?.id;

  if (loading) {
    return <div style={loaderStyle}>Searching active workspaces...</div>;
  }

  return (
    <div style={containerStyle}>
      {!team ? (
        // Create Team Workspace Panel
        <div className="glass-panel animate-fade-in" style={createCardStyle}>
          <div style={iconHeaderStyle}>
            <FiUsers size={48} style={{ color: 'var(--primary)' }} />
          </div>
          <h3 style={centerTitleStyle}>Create a Team Workspace</h3>
          <p style={centerDescStyle}>
            Workspaces let you collaborate with content creators and marketing managers. Organize campaigns and schedule posts together.
          </p>

          {createError && (
            <div style={errorContainerStyle}>
              <FiAlertCircle size={16} />
              <span>{createError}</span>
            </div>
          )}

          <form onSubmit={handleCreateTeam} style={createFormStyle}>
            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label className="form-label" htmlFor="team-name">Workspace Team Name</label>
              <input
                className="form-input"
                id="team-name"
                type="text"
                placeholder="e.g. Marketing Team Alpha"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                disabled={createSubmitting}
              />
            </div>
            <button className="btn-primary" type="submit" disabled={createSubmitting} style={{ width: '100%' }}>
              {createSubmitting ? 'Creating...' : 'Initialize Workspace'}
            </button>
          </form>
        </div>
      ) : (
        // Active Team Console
        <div style={gridStyle}>
          
          {/* Members list */}
          <div className="glass-panel animate-fade-in" style={listCardStyle}>
            <div style={teamTitleRow}>
              <div>
                <h3 style={titleStyle}>{team.name} Workspace</h3>
                <p style={descStyle}>Manage collaborators in your active campaign team</p>
              </div>
              <span style={badgeStyle}>
                <FiShield style={{ marginRight: '4px' }} /> 
                {isOwner ? 'Workspace Owner' : 'Member'}
              </span>
            </div>

            {actionError && (
              <div style={errorContainerStyle}>
                <FiAlertCircle size={16} />
                <span>{actionError}</span>
              </div>
            )}

            {actionSuccess && (
              <div style={successContainerStyle}>
                <FiCheckCircle size={16} />
                <span>{actionSuccess}</span>
              </div>
            )}

            <div style={tableContainerStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr style={tableHeaderRowStyle}>
                    <th style={thStyle}>Name</th>
                    <th style={thStyle}>Email</th>
                    <th style={thStyle}>Role</th>
                    <th style={thStyle}>Status</th>
                    {isOwner && <th style={thRightStyle}>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {team.members.map((member) => {
                    const mId = member.id || member.user_id;
                    const mRole = member.role || member.role_in_team || 'Marketing Team';
                    const isPending = member.status === 'pending';
                    
                    return (
                      <tr key={mId} style={tableRowStyle}>
                        <td style={tdStyle}>
                          <strong>{member.name || member.email}</strong>
                          {(member.user_id === user?.id || member.id === user?.id) && <span style={meBadgeStyle}>You</span>}
                        </td>
                        <td style={tdStyle}>{member.email}</td>
                        <td style={tdStyle}>
                          <span style={roleBadgeStyle(mRole)}>
                            {mRole}
                          </span>
                        </td>
                        <td style={tdStyle}>
                          <span style={isPending ? pendingBadgeStyle : activeBadgeStyle}>
                            {isPending ? 'Pending Invite' : 'Active'}
                          </span>
                        </td>
                        {isOwner && (
                          <td style={tdRightStyle}>
                            {mRole !== 'owner' ? (
                              <button 
                                style={actionBtnStyle} 
                                onClick={() => handleRemoveMember(mId, member.name || member.email)}
                                title={isPending ? "Cancel invitation" : "Remove member"}
                              >
                                <FiTrash2 size={16} />
                              </button>
                            ) : (
                              <span style={mutedTextStyle}>Owner</span>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Invitation Section */}
          {isOwner && (
            <div className="glass-panel animate-fade-in" style={inviteCardStyle}>
              <h3 style={titleStyle}>Invite Member</h3>
              <p style={descStyle}>Add a new member to this team workspace by email</p>

              {inviteError && (
                <div style={errorContainerStyle}>
                  <FiAlertCircle size={16} />
                  <span>{inviteError}</span>
                </div>
              )}

              {inviteSuccess && (
                <div style={successContainerStyle}>
                  <FiCheckCircle size={16} />
                  <span>{inviteSuccess}</span>
                </div>
              )}

              <form onSubmit={handleInviteMember} style={formStyle}>
                <div className="form-group">
                  <label className="form-label" htmlFor="invite-email">Member Email</label>
                  <div style={inputContainerStyle}>
                    <FiMail style={iconStyle} />
                    <input
                      className="form-input"
                      style={inputWithIconStyle}
                      id="invite-email"
                      type="email"
                      placeholder="collaborator@company.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      disabled={inviteSubmitting}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="invite-role">Workspace Role</label>
                  <select
                    className="form-input"
                    id="invite-role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    disabled={inviteSubmitting}
                    style={selectStyle}
                  >
                    <option value="Content Creator">Content Creator</option>
                    <option value="Marketing Team">Marketing Team</option>
                    <option value="Business User">Business User</option>
                    <option value="Administrator">Administrator</option>
                  </select>
                </div>

                <button className="btn-primary" type="submit" disabled={inviteSubmitting} style={buttonStyle}>
                  <FiUserPlus />
                  {inviteSubmitting ? 'Sending...' : 'Invite Member'}
                </button>
              </form>
            </div>
          )}

        </div>
      )}
    </div>
  );
};

const loaderStyle = {
  textAlign: 'center',
  padding: '40px',
  color: 'var(--text-secondary)',
  fontSize: '1rem'
};

const containerStyle = {
  width: '100%',
};

const createCardStyle = {
  maxWidth: '520px',
  margin: '40px auto',
  padding: '40px',
  textAlign: 'center',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
};

const iconHeaderStyle = {
  marginBottom: '20px',
  background: 'rgba(99, 102, 241, 0.1)',
  padding: '20px',
  borderRadius: '50%'
};

const centerTitleStyle = {
  fontSize: '1.5rem',
  marginBottom: '12px'
};

const centerDescStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.9rem',
  lineHeight: '1.6',
  marginBottom: '32px'
};

const createFormStyle = {
  width: '100%',
  textAlign: 'left'
};

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: '3fr 2fr',
  gap: '24px',
  alignItems: 'start'
};

// Fallback for smaller screens to stack grids
if (typeof window !== 'undefined' && window.innerWidth < 960) {
  gridStyle.gridTemplateColumns = '1fr';
}

const listCardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
};

const inviteCardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
};

const teamTitleRow = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  marginBottom: '24px',
  borderBottom: '1px solid var(--border-color)',
  paddingBottom: '20px'
};

const badgeStyle = {
  fontSize: '0.8rem',
  fontWeight: '600',
  color: 'var(--accent)',
  background: 'rgba(6, 182, 212, 0.1)',
  border: '1px solid rgba(6, 182, 212, 0.2)',
  padding: '6px 12px',
  borderRadius: '20px',
  display: 'flex',
  alignItems: 'center'
};

const titleStyle = {
  fontSize: '1.25rem',
  marginBottom: '4px',
};

const descStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  marginBottom: '20px',
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
  fontSize: '0.85rem',
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
  fontSize: '0.85rem',
};

const formStyle = {
  display: 'flex',
  flexDirection: 'column',
};

const inputContainerStyle = {
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
};

const iconStyle = {
  position: 'absolute',
  left: '16px',
  color: 'var(--text-muted)',
};

const inputWithIconStyle = {
  paddingLeft: '44px',
  width: '100%',
};

const selectStyle = {
  width: '100%',
  cursor: 'pointer',
  appearance: 'none',
  backgroundImage: 'url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%2394a3b8\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e")',
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 16px center',
  backgroundSize: '16px',
  paddingRight: '40px'
};

const buttonStyle = {
  marginTop: '12px',
  width: '100%',
};

const tableContainerStyle = {
  overflowX: 'auto',
};

const tableStyle = {
  width: '100%',
  borderCollapse: 'collapse',
  textAlign: 'left',
};

const tableHeaderRowStyle = {
  borderBottom: '2px solid var(--border-color)',
};

const thStyle = {
  padding: '12px 16px',
  color: 'var(--text-secondary)',
  fontSize: '0.85rem',
  fontWeight: '600',
  textTransform: 'uppercase',
  letterSpacing: '0.05em'
};

const thRightStyle = {
  ...thStyle,
  textAlign: 'right'
};

const tableRowStyle = {
  borderBottom: '1px solid var(--border-color)',
};

const tdStyle = {
  padding: '16px',
  fontSize: '0.9rem',
  color: 'var(--text-primary)',
};

const tdRightStyle = {
  ...tdStyle,
  textAlign: 'right'
};

const meBadgeStyle = {
  fontSize: '0.75rem',
  color: 'var(--primary)',
  background: 'rgba(99, 102, 241, 0.1)',
  padding: '2px 6px',
  borderRadius: '4px',
  marginLeft: '8px'
};

const actionBtnStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  cursor: 'pointer',
  padding: '6px',
  borderRadius: '6px',
  transition: 'all 0.2s',
  display: 'inline-flex',
  alignItems: 'center'
};

// Hover animation inside document
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.innerHTML = `
    tr:hover button { color: #f43f5e !important; background: rgba(244, 63, 94, 0.05); }
  `;
  document.head.appendChild(style);
}

const mutedTextStyle = {
  fontSize: '0.8rem',
  color: 'var(--text-muted)'
};

const roleBadgeStyle = (role) => {
  let color = 'var(--text-secondary)';
  let bg = 'rgba(255, 255, 255, 0.03)';
  
  if (role === 'owner' || role === 'Administrator') {
    color = 'var(--accent)';
    bg = 'rgba(6, 182, 212, 0.08)';
  } else if (role === 'Business User') {
    color = 'var(--primary)';
    bg = 'rgba(99, 102, 241, 0.08)';
  } else if (role === 'Marketing Team') {
    color = 'var(--secondary)';
    bg = 'rgba(168, 85, 247, 0.08)';
  }
  
  return {
    fontSize: '0.8rem',
    fontWeight: '500',
    color: color,
    background: bg,
    padding: '4px 10px',
    borderRadius: '6px',
  };
};

const activeBadgeStyle = {
  fontSize: '0.75rem',
  color: 'var(--success)',
  background: 'rgba(16, 185, 129, 0.1)',
  padding: '3px 8px',
  borderRadius: '12px',
  fontWeight: '600'
};

const pendingBadgeStyle = {
  fontSize: '0.75rem',
  color: 'var(--warning)',
  background: 'rgba(245, 158, 11, 0.1)',
  padding: '3px 8px',
  borderRadius: '12px',
  fontWeight: '600'
};

export default TeamManagement;

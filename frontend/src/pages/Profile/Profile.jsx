import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { FiUser, FiPhone, FiLock, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';

const Profile = () => {
  const { user, refreshProfile } = useAuth();
  
  // Profile state
  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');
  const [profileSubmitting, setProfileSubmitting] = useState(false);

  // Password state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState('');
  const [pwdSubmitting, setPwdSubmitting] = useState(false);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileError('');
    setProfileSuccess('');

    if (!name) {
      setProfileError('Name cannot be empty');
      return;
    }

    setProfileSubmitting(true);
    try {
      await api.put('/profile', { name, phone });
      await refreshProfile();
      setProfileSuccess('Profile updated successfully!');
    } catch (err) {
      setProfileError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setProfileSubmitting(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdError('');
    setPwdSuccess('');

    if (!oldPassword || !newPassword || !confirmNewPassword) {
      setPwdError('Please fill in all fields');
      return;
    }

    if (newPassword.length < 8) {
      setPwdError('New password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setPwdError('New passwords do not match');
      return;
    }

    setPwdSubmitting(true);
    try {
      await api.put('/profile/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword
      });
      
      setPwdSuccess('Password changed successfully!');
      setOldPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err) {
      setPwdError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setPwdSubmitting(false);
    }
  };

  return (
    <div style={containerStyle}>
      <div style={gridStyle}>
        
        {/* Profile Card */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <h3 style={titleStyle}>Profile Information</h3>
          <p style={descStyle}>Update your user details and phone registration</p>

          {profileError && (
            <div style={errorContainerStyle}>
              <FiAlertCircle size={16} />
              <span>{profileError}</span>
            </div>
          )}

          {profileSuccess && (
            <div style={successContainerStyle}>
              <FiCheckCircle size={16} />
              <span>{profileSuccess}</span>
            </div>
          )}

          <form onSubmit={handleUpdateProfile} style={formStyle}>
            <div className="form-group">
              <label className="form-label" htmlFor="email-read">Email Address (Read-only)</label>
              <input
                className="form-input"
                style={readOnlyInputStyle}
                id="email-read"
                type="email"
                value={user?.email || ''}
                readOnly
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="role-read">System Role (Read-only)</label>
              <input
                className="form-input"
                style={readOnlyInputStyle}
                id="role-read"
                type="text"
                value={user?.role_name || user?.role?.name || ''}
                readOnly
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="profile-name">Full Name</label>
              <div style={inputContainerStyle}>
                <FiUser style={iconStyle} />
                <input
                  className="form-input"
                  style={inputWithIconStyle}
                  id="profile-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={profileSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="profile-phone">Phone Number</label>
              <div style={inputContainerStyle}>
                <FiPhone style={iconStyle} />
                <input
                  className="form-input"
                  style={inputWithIconStyle}
                  id="profile-phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={profileSubmitting}
                />
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={profileSubmitting} style={buttonStyle}>
              {profileSubmitting ? 'Updating...' : 'Save Changes'}
            </button>
          </form>
        </div>

        {/* Password Card */}
        <div className="glass-panel animate-fade-in" style={cardStyle}>
          <h3 style={titleStyle}>Change Password</h3>
          <p style={descStyle}>Ensure your account is using a secure, long password</p>

          {pwdError && (
            <div style={errorContainerStyle}>
              <FiAlertCircle size={16} />
              <span>{pwdError}</span>
            </div>
          )}

          {pwdSuccess && (
            <div style={successContainerStyle}>
              <FiCheckCircle size={16} />
              <span>{pwdSuccess}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} style={formStyle}>
            <div className="form-group">
              <label className="form-label" htmlFor="old-pass">Current Password</label>
              <div style={inputContainerStyle}>
                <FiLock style={iconStyle} />
                <input
                  className="form-input"
                  style={inputWithIconStyle}
                  id="old-pass"
                  type="password"
                  placeholder="••••••••"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  disabled={pwdSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="new-pass">New Password (Min 8 chars)</label>
              <div style={inputContainerStyle}>
                <FiLock style={iconStyle} />
                <input
                  className="form-input"
                  style={inputWithIconStyle}
                  id="new-pass"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={pwdSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="confirm-new-pass">Confirm New Password</label>
              <div style={inputContainerStyle}>
                <FiLock style={iconStyle} />
                <input
                  className="form-input"
                  style={inputWithIconStyle}
                  id="confirm-new-pass"
                  type="password"
                  placeholder="••••••••"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  disabled={pwdSubmitting}
                />
              </div>
            </div>

            <button className="btn-primary" type="submit" disabled={pwdSubmitting} style={buttonStyle}>
              {pwdSubmitting ? 'Updating Password...' : 'Update Password'}
            </button>
          </form>
        </div>

      </div>
    </div>
  );
};

const containerStyle = {
  width: '100%',
};

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
  gap: '24px',
};

const cardStyle = {
  padding: '32px',
  display: 'flex',
  flexDirection: 'column',
};

const titleStyle = {
  fontSize: '1.25rem',
  marginBottom: '4px',
};

const descStyle = {
  fontSize: '0.85rem',
  color: 'var(--text-secondary)',
  marginBottom: '24px',
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

const readOnlyInputStyle = {
  opacity: 0.6,
  cursor: 'not-allowed',
  backgroundColor: 'rgba(255, 255, 255, 0.02)'
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

const buttonStyle = {
  marginTop: '12px',
  width: '100%',
};

export default Profile;

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiLock, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

const ResetPassword = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setSubmitting(true);
    // Simulate reset completion API call
    setTimeout(() => {
      setSuccess(true);
      setSubmitting(false);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    }, 1200);
  };

  return (
    <div style={containerStyle}>
      <div className="glass-panel animate-fade-in" style={cardStyle}>
        <div style={headerStyle}>
          <h2 style={titleStyle}>Reset Password</h2>
          <p style={subtitleStyle}>Enter your new password below</p>
        </div>

        {error && (
          <div style={errorContainerStyle}>
            <FiAlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={successContainerStyle}>
            <FiCheckCircle size={18} />
            <span>Password updated successfully! Redirecting to login...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={formStyle}>
          <div className="form-group">
            <label className="form-label" htmlFor="password">New Password</label>
            <div style={inputContainerStyle}>
              <FiLock style={iconStyle} />
              <input
                className="form-input"
                style={inputWithIconStyle}
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={submitting || success}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
            <div style={inputContainerStyle}>
              <FiLock style={iconStyle} />
              <input
                className="form-input"
                style={inputWithIconStyle}
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={submitting || success}
              />
            </div>
          </div>

          <button className="btn-primary" type="submit" style={buttonStyle} disabled={submitting || success}>
            {submitting ? 'Updating password...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

const containerStyle = {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  padding: '20px',
};

const cardStyle = {
  width: '100%',
  maxWidth: '440px',
  padding: '40px',
  display: 'flex',
  flexDirection: 'column',
};

const headerStyle = {
  textAlign: 'center',
  marginBottom: '32px',
};

const titleStyle = {
  fontSize: '2rem',
  background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  marginBottom: '8px',
};

const subtitleStyle = {
  fontSize: '0.9rem',
  color: 'var(--text-secondary)',
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
  fontSize: '0.9rem',
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
  fontSize: '0.9rem',
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

const buttonStyle = {
  marginTop: '12px',
  width: '100%',
};

export default ResetPassword;

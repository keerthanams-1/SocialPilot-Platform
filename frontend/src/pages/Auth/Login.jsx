import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FiMail, FiLock, FiAlertCircle } from 'react-icons/fi';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectPath = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setSubmitting(true);
    try {
      await login(email, password);
      navigate(redirectPath, { replace: true });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid email or password';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={containerStyle}>
      <div className="glass-panel animate-fade-in" style={cardStyle}>
        <div style={headerStyle}>
          <h2 style={titleStyle}>SocialPilot</h2>
          <p style={subtitleStyle}>Access your social scheduling platform</p>
        </div>

        {error && (
          <div style={errorContainerStyle}>
            <FiAlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={formStyle}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <div style={inputContainerStyle}>
              <FiMail style={iconStyle} />
              <input
                className="form-input"
                style={inputWithIconStyle}
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting}
              />
            </div>
          </div>

          <div className="form-group">
            <div style={labelRowStyle}>
              <label className="form-label" htmlFor="password">Password</label>
              <Link to="/forgot-password" style={forgotLinkStyle}>Forgot?</Link>
            </div>
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
                disabled={submitting}
              />
            </div>
          </div>

          <button className="btn-primary" type="submit" style={buttonStyle} disabled={submitting}>
            {submitting ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        {/* 1-CLICK DEMO ROLE LOGIN SHORTCUTS */}
        <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--border-color)' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', textAlign: 'center', marginBottom: '12px', fontWeight: 'bold' }}>
            ⚡ 1-CLICK QUICK DEMO LOGIN BY ROLE
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button
              type="button"
              onClick={() => { setEmail('admin@socialpilot.com'); setPassword('admin123'); }}
              style={{ padding: '8px 10px', fontSize: '0.74rem', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.12)', color: '#ef4444', fontWeight: 'bold', cursor: 'pointer', textAlign: 'left' }}
            >
              🛡️ Admin User
            </button>
            <button
              type="button"
              onClick={() => { setEmail('creator@socialpilot.com'); setPassword('creator123'); }}
              style={{ padding: '8px 10px', fontSize: '0.74rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.4)', background: 'rgba(16, 185, 129, 0.12)', color: '#10b981', fontWeight: 'bold', cursor: 'pointer', textAlign: 'left' }}
            >
              ✍️ Content Creator
            </button>
            <button
              type="button"
              onClick={() => { setEmail('marketing@socialpilot.com'); setPassword('marketing123'); }}
              style={{ padding: '8px 10px', fontSize: '0.74rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.4)', background: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b', fontWeight: 'bold', cursor: 'pointer', textAlign: 'left' }}
            >
              📣 Marketing Spec
            </button>
            <button
              type="button"
              onClick={() => { setEmail('business@socialpilot.com'); setPassword('business123'); }}
              style={{ padding: '8px 10px', fontSize: '0.74rem', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.4)', background: 'rgba(59, 130, 246, 0.12)', color: '#3b82f6', fontWeight: 'bold', cursor: 'pointer', textAlign: 'left' }}
            >
              🏢 Business User
            </button>
          </div>
        </div>

        <div style={footerStyle}>
          <span style={footerTextStyle}>New to SocialPilot? </span>
          <Link to="/register" style={registerLinkStyle}>Create account</Link>
        </div>
      </div>
    </div>
  );
};

// Inline layouts and positioning overrides
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

const labelRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

const forgotLinkStyle = {
  fontSize: '0.8rem',
  color: 'var(--primary)',
  textDecoration: 'none',
  fontWeight: '500',
};

const buttonStyle = {
  marginTop: '12px',
  width: '100%',
};

const footerStyle = {
  textAlign: 'center',
  marginTop: '28px',
  fontSize: '0.9rem',
};

const footerTextStyle = {
  color: 'var(--text-secondary)',
};

const registerLinkStyle = {
  color: 'var(--primary)',
  textDecoration: 'none',
  fontWeight: '600',
};

export default Login;

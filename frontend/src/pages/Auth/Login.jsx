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

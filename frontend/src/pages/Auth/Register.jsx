import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FiUser, FiMail, FiLock, FiPhone, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [roleName, setRoleName] = useState('Content Creator');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name || !email || !password || !confirmPassword) {
      setError('Please fill in all required fields');
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
    try {
      await register(name, email, password, confirmPassword, roleName);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed. Try again.';
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
          <p style={subtitleStyle}>Create your account to get started</p>
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
            <span>Account created successfully! Redirecting...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={formStyle}>
          <div className="form-group">
            <label className="form-label" htmlFor="name">Full Name *</label>
            <div style={inputContainerStyle}>
              <FiUser style={iconStyle} />
              <input
                className="form-input"
                style={inputWithIconStyle}
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={submitting || success}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address *</label>
            <div style={inputContainerStyle}>
              <FiMail style={iconStyle} />
              <input
                className="form-input"
                style={inputWithIconStyle}
                id="email"
                type="email"
                placeholder="john@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting || success}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="phone">Phone Number (Optional)</label>
            <div style={inputContainerStyle}>
              <FiPhone style={iconStyle} />
              <input
                className="form-input"
                style={inputWithIconStyle}
                id="phone"
                type="tel"
                placeholder="+1 (555) 000-0000"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={submitting || success}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="role">Default Workspace Role</label>
            <select
              className="form-input"
              id="role"
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              disabled={submitting || success}
              style={selectStyle}
            >
              <option value="Content Creator">Content Creator</option>
              <option value="Marketing Team">Marketing Team</option>
              <option value="Business User">Business User</option>
              <option value="Administrator">Administrator</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password * (Min 8 chars)</label>
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
            <label className="form-label" htmlFor="confirmPassword">Confirm Password *</label>
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
            {submitting ? 'Registering...' : 'Sign Up'}
          </button>
        </form>

        <div style={footerStyle}>
          <span style={footerTextStyle}>Already have an account? </span>
          <Link to="/login" style={loginLinkStyle}>Sign in</Link>
        </div>
      </div>
    </div>
  );
};

// Styles mapped to Register Page elements
const containerStyle = {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  padding: '40px 20px',
};

const cardStyle = {
  width: '100%',
  maxWidth: '460px',
  padding: '40px',
  display: 'flex',
  flexDirection: 'column',
};

const headerStyle = {
  textAlign: 'center',
  marginBottom: '28px',
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
  marginTop: '16px',
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

const loginLinkStyle = {
  color: 'var(--primary)',
  textDecoration: 'none',
  fontWeight: '600',
};

export default Register;

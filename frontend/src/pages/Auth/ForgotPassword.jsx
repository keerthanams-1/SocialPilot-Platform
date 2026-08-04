import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiMail, FiArrowLeft, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Please provide your email address');
      return;
    }

    setSubmitting(true);
    // Simulate reset email API call
    setTimeout(() => {
      setSuccess(true);
      setSubmitting(false);
    }, 1200);
  };

  return (
    <div style={containerStyle}>
      <div className="glass-panel animate-fade-in" style={cardStyle}>
        <div style={headerStyle}>
          <h2 style={titleStyle}>Recover Password</h2>
          <p style={subtitleStyle}>We'll send you instructions to reset your password</p>
        </div>

        {error && (
          <div style={errorContainerStyle}>
            <FiAlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div style={successStateStyle}>
            <FiCheckCircle size={44} style={successIconStyle} />
            <h3 style={successTitleStyle}>Check your inbox</h3>
            <p style={successDescStyle}>
              We sent a simulated recovery link to <strong>{email}</strong>. Use it to reset your credentials.
            </p>
            <Link to="/login" className="btn-secondary" style={backToLoginBtnStyle}>
              <FiArrowLeft /> Back to login
            </Link>
          </div>
        ) : (
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

            <button className="btn-primary" type="submit" style={buttonStyle} disabled={submitting}>
              {submitting ? 'Sending instructions...' : 'Send Recovery Link'}
            </button>

            <Link to="/login" style={backLinkStyle}>
              <FiArrowLeft size={16} /> Back to Sign In
            </Link>
          </form>
        )}
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

const backLinkStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '8px',
  marginTop: '24px',
  fontSize: '0.9rem',
  color: 'var(--text-secondary)',
  textDecoration: 'none',
  fontWeight: '500',
  transition: 'color 0.2s',
};

const successStateStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  textAlign: 'center',
};

const successIconStyle = {
  color: 'var(--success)',
  marginBottom: '16px',
};

const successTitleStyle = {
  fontSize: '1.25rem',
  marginBottom: '12px',
};

const successDescStyle = {
  color: 'var(--text-secondary)',
  fontSize: '0.9rem',
  lineHeight: '1.6',
  marginBottom: '24px',
};

const backToLoginBtnStyle = {
  width: '100%',
  textDecoration: 'none',
};

export default ForgotPassword;

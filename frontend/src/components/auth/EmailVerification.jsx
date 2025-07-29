import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const EmailVerification = () => {
  const [searchParams] = useSearchParams();
  const [verificationStatus, setVerificationStatus] = useState('verifying');
  const [error, setError] = useState('');
  const { verifyEmail, authService } = useAuth();

  const token = searchParams.get('token');
  const email = searchParams.get('email');

  useEffect(() => {
    const handleVerification = async () => {
      if (!token) {
        setVerificationStatus('error');
        setError('Invalid verification link');
        return;
      }

      try {
        await verifyEmail(token);
        setVerificationStatus('success');
      } catch (error) {
        setVerificationStatus('error');
        setError(error.message);
      }
    };

    handleVerification();
  }, [token, verifyEmail]);

  const handleResendVerification = async () => {
    if (!email) {
      setError('Email address not found');
      return;
    }

    try {
      await authService.resendVerification(email);
      setVerificationStatus('resent');
    } catch (error) {
      setError(error.message);
    }
  };

  if (verificationStatus === 'verifying') {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <div className="auth-header">
            <h2>Verifying Email</h2>
            <p>Please wait while we verify your email address</p>
          </div>
          <div className="loading-container">
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>Verifying...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (verificationStatus === 'success') {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <div className="auth-header">
            <h2>Email Verified!</h2>
            <p>Your email has been successfully verified</p>
          </div>
          <div className="success-message">
            <div className="success-icon">✅</div>
            <p>Your email address has been verified successfully.</p>
            <p>You can now sign in to your account.</p>
          </div>
          <div className="auth-footer">
            <Link to="/login" className="auth-submit-btn">
              Sign In Now
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (verificationStatus === 'resent') {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <div className="auth-header">
            <h2>Verification Email Sent</h2>
            <p>Please check your email for the new verification link</p>
          </div>
          <div className="success-message">
            <div className="success-icon">📧</div>
            <p>A new verification email has been sent to {email}</p>
            <p>Please check your inbox and click the verification link.</p>
          </div>
          <div className="auth-footer">
            <Link to="/login" className="auth-link">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2>Verification Failed</h2>
          <p>We couldn't verify your email address</p>
        </div>
        <div className="error-message">
          <div className="error-icon">❌</div>
          <p>{error}</p>
          {email && (
            <p>
              <button
                type="button"
                className="link-button"
                onClick={handleResendVerification}
              >
                Resend verification email
              </button>
            </p>
          )}
        </div>
        <div className="auth-footer">
          <Link to="/login" className="auth-link">
            Back to Login
          </Link>
          <Link to="/register" className="auth-link">
            Create New Account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '../../contexts/AuthContext';
import { resetPasswordSchema } from '../../utils/validators';
import { Link } from 'react-router-dom';

const ForgotPasswordForm = () => {
  const [resetSent, setResetSent] = useState(false);
  const { resetPassword, isLoading } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    watch,
  } = useForm({
    resolver: zodResolver(resetPasswordSchema),
  });

  const watchedEmail = watch('email');

  const onSubmit = async (data) => {
    try {
      await resetPassword(data.email);
      setResetSent(true);
    } catch (error) {
      setError('root', {
        type: 'manual',
        message: error.message,
      });
    }
  };

  if (resetSent) {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <div className="auth-header">
            <h2>Check Your Email</h2>
            <p>Password reset instructions sent</p>
          </div>
          <div className="success-message">
            <div className="success-icon">📧</div>
            <p>
              We've sent password reset instructions to <strong>{watchedEmail}</strong>
            </p>
            <p>Please check your email and follow the instructions to reset your password.</p>
            <p className="note">
              If you don't see the email, check your spam folder or{' '}
              <button
                type="button"
                className="link-button"
                onClick={() => setResetSent(false)}
              >
                try again
              </button>
            </p>
          </div>
          <div className="auth-footer">
            <p>
              Remember your password?{' '}
              <Link to="/login" className="auth-link">
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2>Forgot Password?</h2>
          <p>Enter your email to receive reset instructions</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="auth-form-content">
          {errors.root && (
            <div className="error-message">
              {errors.root.message}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              {...register('email')}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email address"
              autoComplete="email"
            />
            {errors.email && (
              <span className="field-error">{errors.email.message}</span>
            )}
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isSubmitting || isLoading}
          >
            {isSubmitting || isLoading ? (
              <span className="loading-spinner">Sending...</span>
            ) : (
              'Send Reset Instructions'
            )}
          </button>

          <div className="auth-footer">
            <p>
              Remember your password?{' '}
              <Link to="/login" className="auth-link">
                Sign in here
              </Link>
            </p>
            <p>
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">
                Sign up here
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ForgotPasswordForm;
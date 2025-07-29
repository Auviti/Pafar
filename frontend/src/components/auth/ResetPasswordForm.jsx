import React, { useState, useRef, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '../../contexts/AuthContext';
import { confirmResetPasswordSchema } from '../../utils/validators';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

const OTPInput = ({ value, onChange, error }) => {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (value && value.length === 6) {
      setOtp(value.split(''));
    }
  }, [value]);

  const handleChange = (index, val) => {
    if (val.length > 1) return;
    
    const newOtp = [...otp];
    newOtp[index] = val;
    setOtp(newOtp);
    onChange(newOtp.join(''));

    // Auto-focus next input
    if (val && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    if (/^\d+$/.test(pastedData)) {
      const newOtp = pastedData.split('').concat(Array(6 - pastedData.length).fill(''));
      setOtp(newOtp);
      onChange(pastedData);
    }
  };

  return (
    <div className="otp-container">
      <div className="otp-inputs">
        {otp.map((digit, index) => (
          <input
            key={index}
            ref={(el) => (inputRefs.current[index] = el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onPaste={handlePaste}
            className={`otp-input ${error ? 'error' : ''}`}
            autoComplete="one-time-code"
          />
        ))}
      </div>
      {error && <span className="field-error">{error}</span>}
    </div>
  );
};

const ResetPasswordForm = () => {
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);
  const { confirmResetPassword, isLoading } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const emailFromUrl = searchParams.get('email');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    setValue,
    watch,
  } = useForm({
    resolver: zodResolver(confirmResetPasswordSchema),
  });

  const watchedToken = watch('token');

  const onSubmit = async (data) => {
    try {
      await confirmResetPassword(data.token, data.newPassword);
      setResetSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error) {
      setError('root', {
        type: 'manual',
        message: error.message,
      });
    }
  };

  if (resetSuccess) {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <div className="auth-header">
            <h2>Password Reset Successful!</h2>
            <p>Your password has been updated</p>
          </div>
          <div className="success-message">
            <div className="success-icon">✅</div>
            <p>Your password has been successfully reset.</p>
            <p>You will be redirected to the login page in a few seconds.</p>
          </div>
          <div className="auth-footer">
            <Link to="/login" className="auth-link">
              Go to Login
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
          <h2>Reset Your Password</h2>
          <p>Enter the verification code and your new password</p>
          {emailFromUrl && (
            <p className="email-hint">Code sent to: {emailFromUrl}</p>
          )}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="auth-form-content">
          {errors.root && (
            <div className="error-message">
              {errors.root.message}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="token">Verification Code</label>
            <OTPInput
              value={watchedToken || ''}
              onChange={(value) => setValue('token', value)}
              error={errors.token?.message}
            />
            <p className="form-hint">
              Enter the 6-digit code sent to your email
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <div className="password-input-container">
              <input
                id="newPassword"
                type={showNewPassword ? 'text' : 'password'}
                {...register('newPassword')}
                className={errors.newPassword ? 'error' : ''}
                placeholder="Enter your new password"
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowNewPassword(!showNewPassword)}
                aria-label={showNewPassword ? 'Hide password' : 'Show password'}
              >
                {showNewPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.newPassword && (
              <span className="field-error">{errors.newPassword.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm New Password</label>
            <div className="password-input-container">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                {...register('confirmPassword')}
                className={errors.confirmPassword ? 'error' : ''}
                placeholder="Confirm your new password"
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.confirmPassword && (
              <span className="field-error">{errors.confirmPassword.message}</span>
            )}
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isSubmitting || isLoading}
          >
            {isSubmitting || isLoading ? (
              <span className="loading-spinner">Resetting Password...</span>
            ) : (
              'Reset Password'
            )}
          </button>

          <div className="auth-footer">
            <p>
              Remember your password?{' '}
              <Link to="/login" className="auth-link">
                Sign in here
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPasswordForm;
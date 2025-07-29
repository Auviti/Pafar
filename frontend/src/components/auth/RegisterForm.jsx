import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '../../contexts/AuthContext';
import { registerSchema } from '../../utils/validators';
import { Link, useNavigate } from 'react-router-dom';

const RegisterForm = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const { register: registerUser, isLoading } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    watch,
  } = useForm({
    resolver: zodResolver(registerSchema),
  });

  const watchedEmail = watch('email');

  const onSubmit = async (data) => {
    try {
      const registrationData = {
        first_name: data.firstName,
        last_name: data.lastName,
        email: data.email,
        phone: data.phone,
        password: data.password,
      };

      await registerUser(registrationData);
      setRegistrationSuccess(true);
    } catch (error) {
      setError('root', {
        type: 'manual',
        message: error.message,
      });
    }
  };

  if (registrationSuccess) {
    return (
      <div className="auth-form-container">
        <div className="auth-form">
          <div className="auth-header">
            <h2>Registration Successful!</h2>
            <p>Please check your email to verify your account</p>
          </div>
          <div className="success-message">
            <div className="success-icon">✅</div>
            <p>
              We've sent a verification email to <strong>{watchedEmail}</strong>
            </p>
            <p>Please click the verification link in your email to activate your account.</p>
          </div>
          <div className="auth-footer">
            <p>
              Already verified?{' '}
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
          <h2>Create Account</h2>
          <p>Join us to start booking your trips</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="auth-form-content">
          {errors.root && (
            <div className="error-message">
              {errors.root.message}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="firstName">First Name</label>
              <input
                id="firstName"
                type="text"
                {...register('firstName')}
                className={errors.firstName ? 'error' : ''}
                placeholder="Enter your first name"
                autoComplete="given-name"
              />
              {errors.firstName && (
                <span className="field-error">{errors.firstName.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="lastName">Last Name</label>
              <input
                id="lastName"
                type="text"
                {...register('lastName')}
                className={errors.lastName ? 'error' : ''}
                placeholder="Enter your last name"
                autoComplete="family-name"
              />
              {errors.lastName && (
                <span className="field-error">{errors.lastName.message}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              {...register('email')}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email"
              autoComplete="email"
            />
            {errors.email && (
              <span className="field-error">{errors.email.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              id="phone"
              type="tel"
              {...register('phone')}
              className={errors.phone ? 'error' : ''}
              placeholder="Enter your phone number"
              autoComplete="tel"
            />
            {errors.phone && (
              <span className="field-error">{errors.phone.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input-container">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                {...register('password')}
                className={errors.password ? 'error' : ''}
                placeholder="Create a password"
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.password && (
              <span className="field-error">{errors.password.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <div className="password-input-container">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                {...register('confirmPassword')}
                className={errors.confirmPassword ? 'error' : ''}
                placeholder="Confirm your password"
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

          <div className="form-options">
            <label className="checkbox-container">
              <input type="checkbox" required />
              <span className="checkmark"></span>
              I agree to the{' '}
              <Link to="/terms" className="auth-link">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link to="/privacy" className="auth-link">
                Privacy Policy
              </Link>
            </label>
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isSubmitting || isLoading}
          >
            {isSubmitting || isLoading ? (
              <span className="loading-spinner">Creating Account...</span>
            ) : (
              'Create Account'
            )}
          </button>

          <div className="auth-footer">
            <p>
              Already have an account?{' '}
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

export default RegisterForm;
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '../../contexts/AuthContext';
import { loginSchema } from '../../utils/validators';
import { Link, useNavigate, useLocation } from 'react-router-dom';

const LoginForm = () => {
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data) => {
    try {
      await login(data);
      navigate(from, { replace: true });
    } catch (error) {
      setError('root', {
        type: 'manual',
        message: error.message,
      });
    }
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <div className="auth-header">
          <h2>Welcome Back</h2>
          <p>Sign in to your account to continue</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="auth-form-content">
          {(error || errors.root) && (
            <div className="error-message">
              {error || errors.root?.message}
            </div>
          )}

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
            <label htmlFor="password">Password</label>
            <div className="password-input-container">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                {...register('password')}
                className={errors.password ? 'error' : ''}
                placeholder="Enter your password"
                autoComplete="current-password"
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

          <div className="form-options">
            <label className="checkbox-container">
              <input type="checkbox" />
              <span className="checkmark"></span>
              Remember me
            </label>
            <Link to="/forgot-password" className="forgot-password-link">
              Forgot Password?
            </Link>
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isSubmitting || isLoading}
          >
            {isSubmitting || isLoading ? (
              <span className="loading-spinner">Signing in...</span>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="auth-footer">
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

export default LoginForm;
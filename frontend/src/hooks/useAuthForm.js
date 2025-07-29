import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Custom hook for handling authentication forms with common functionality
 * @param {Object} options - Configuration options
 * @param {Function} options.onSuccess - Callback function called on successful authentication
 * @param {Function} options.onError - Callback function called on authentication error
 * @returns {Object} Authentication form utilities
 */
export const useAuthForm = ({ onSuccess, onError } = {}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const auth = useAuth();

  const handleSubmit = async (authFunction, data) => {
    try {
      setIsSubmitting(true);
      setFormError(null);
      
      const result = await authFunction(data);
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      return result;
    } catch (error) {
      const errorMessage = error.message || 'An unexpected error occurred';
      setFormError(errorMessage);
      
      if (onError) {
        onError(error);
      }
      
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const clearError = () => {
    setFormError(null);
  };

  return {
    ...auth,
    isSubmitting: isSubmitting || auth.isLoading,
    formError: formError || auth.error,
    handleSubmit,
    clearError,
  };
};

/**
 * Custom hook for handling login form
 */
export const useLoginForm = ({ onSuccess, onError } = {}) => {
  const authForm = useAuthForm({ onSuccess, onError });

  const login = async (credentials) => {
    return authForm.handleSubmit(authForm.login, credentials);
  };

  return {
    ...authForm,
    login,
  };
};

/**
 * Custom hook for handling registration form
 */
export const useRegisterForm = ({ onSuccess, onError } = {}) => {
  const authForm = useAuthForm({ onSuccess, onError });

  const register = async (userData) => {
    return authForm.handleSubmit(authForm.register, userData);
  };

  return {
    ...authForm,
    register,
  };
};

/**
 * Custom hook for handling password reset form
 */
export const usePasswordResetForm = ({ onSuccess, onError } = {}) => {
  const authForm = useAuthForm({ onSuccess, onError });

  const resetPassword = async (email) => {
    return authForm.handleSubmit(authForm.resetPassword, email);
  };

  const confirmResetPassword = async (token, newPassword) => {
    return authForm.handleSubmit(
      (data) => authForm.confirmResetPassword(data.token, data.newPassword),
      { token, newPassword }
    );
  };

  return {
    ...authForm,
    resetPassword,
    confirmResetPassword,
  };
};

/**
 * Custom hook for handling email verification
 */
export const useEmailVerification = ({ onSuccess, onError } = {}) => {
  const authForm = useAuthForm({ onSuccess, onError });

  const verifyEmail = async (token) => {
    return authForm.handleSubmit(authForm.verifyEmail, token);
  };

  const resendVerification = async (email) => {
    return authForm.handleSubmit(authForm.authService.resendVerification, email);
  };

  return {
    ...authForm,
    verifyEmail,
    resendVerification,
  };
};
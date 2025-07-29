/**
 * Authentication utility functions
 */

/**
 * Maps API error codes to user-friendly messages
 */
export const AUTH_ERROR_MESSAGES = {
  INVALID_CREDENTIALS: 'Invalid email or password. Please try again.',
  USER_NOT_FOUND: 'No account found with this email address.',
  EMAIL_ALREADY_EXISTS: 'An account with this email already exists.',
  WEAK_PASSWORD: 'Password is too weak. Please choose a stronger password.',
  INVALID_TOKEN: 'Invalid or expired verification token.',
  TOKEN_EXPIRED: 'Your session has expired. Please sign in again.',
  EMAIL_NOT_VERIFIED: 'Please verify your email address before signing in.',
  ACCOUNT_SUSPENDED: 'Your account has been suspended. Please contact support.',
  TOO_MANY_ATTEMPTS: 'Too many failed attempts. Please try again later.',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
};

/**
 * Gets a user-friendly error message from an error object
 * @param {Error|Object} error - The error object
 * @returns {string} User-friendly error message
 */
export const getAuthErrorMessage = (error) => {
  if (!error) return 'An unexpected error occurred';

  // If error has a message property, use it
  if (error.message) {
    // Check if the message matches any known error codes
    const errorCode = Object.keys(AUTH_ERROR_MESSAGES).find(code => 
      error.message.includes(code) || error.message.includes(code.toLowerCase())
    );
    
    if (errorCode) {
      return AUTH_ERROR_MESSAGES[errorCode];
    }
    
    return error.message;
  }

  // If error has response data (axios error)
  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  // If error has response data with error code
  if (error.response?.data?.error?.code) {
    const errorCode = error.response.data.error.code;
    return AUTH_ERROR_MESSAGES[errorCode] || error.response.data.error.message || 'An error occurred';
  }

  return 'An unexpected error occurred';
};

/**
 * Validates password strength
 * @param {string} password - The password to validate
 * @returns {Object} Validation result with isValid and errors
 */
export const validatePasswordStrength = (password) => {
  const errors = [];
  
  if (!password) {
    errors.push('Password is required');
    return { isValid: false, errors };
  }

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validates email format
 * @param {string} email - The email to validate
 * @returns {boolean} True if email is valid
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validates phone number format
 * @param {string} phone - The phone number to validate
 * @returns {boolean} True if phone number is valid
 */
export const validatePhoneNumber = (phone) => {
  const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
  return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
};

/**
 * Formats phone number for display
 * @param {string} phone - The phone number to format
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phone) => {
  const cleaned = phone.replace(/\D/g, '');
  
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  
  if (cleaned.length === 11 && cleaned[0] === '1') {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  
  return phone;
};

/**
 * Checks if user session is expired based on token
 * @param {string} token - JWT token
 * @returns {boolean} True if token is expired
 */
export const isTokenExpired = (token) => {
  if (!token) return true;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch (error) {
    return true;
  }
};

/**
 * Gets user role from token
 * @param {string} token - JWT token
 * @returns {string|null} User role or null if invalid
 */
export const getUserRoleFromToken = (token) => {
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.role || null;
  } catch (error) {
    return null;
  }
};

/**
 * Generates a secure random password
 * @param {number} length - Password length (default: 12)
 * @returns {string} Generated password
 */
export const generateSecurePassword = (length = 12) => {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const numbers = '0123456789';
  const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?';
  
  const allChars = lowercase + uppercase + numbers + symbols;
  let password = '';
  
  // Ensure at least one character from each category
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];
  password += symbols[Math.floor(Math.random() * symbols.length)];
  
  // Fill the rest randomly
  for (let i = 4; i < length; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)];
  }
  
  // Shuffle the password
  return password.split('').sort(() => Math.random() - 0.5).join('');
};

/**
 * Debounce function for form validation
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};

/**
 * Storage utilities for authentication data
 */
export const authStorage = {
  /**
   * Stores authentication data securely
   * @param {string} key - Storage key
   * @param {any} value - Value to store
   */
  setItem: (key, value) => {
    try {
      localStorage.setItem(`auth_${key}`, JSON.stringify(value));
    } catch (error) {
      console.warn('Failed to store auth data:', error);
    }
  },

  /**
   * Retrieves authentication data
   * @param {string} key - Storage key
   * @returns {any} Stored value or null
   */
  getItem: (key) => {
    try {
      const item = localStorage.getItem(`auth_${key}`);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.warn('Failed to retrieve auth data:', error);
      return null;
    }
  },

  /**
   * Removes authentication data
   * @param {string} key - Storage key
   */
  removeItem: (key) => {
    try {
      localStorage.removeItem(`auth_${key}`);
    } catch (error) {
      console.warn('Failed to remove auth data:', error);
    }
  },

  /**
   * Clears all authentication data
   */
  clear: () => {
    try {
      const keys = Object.keys(localStorage).filter(key => key.startsWith('auth_'));
      keys.forEach(key => localStorage.removeItem(key));
    } catch (error) {
      console.warn('Failed to clear auth data:', error);
    }
  },
};
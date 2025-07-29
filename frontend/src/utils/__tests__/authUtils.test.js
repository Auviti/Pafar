import { vi } from 'vitest';
import {
  getAuthErrorMessage,
  validatePasswordStrength,
  validateEmail,
  validatePhoneNumber,
  formatPhoneNumber,
  isTokenExpired,
  getUserRoleFromToken,
  generateSecurePassword,
  debounce,
  authStorage,
  AUTH_ERROR_MESSAGES,
} from '../authUtils';

describe('getAuthErrorMessage', () => {
  it('should return default message for null/undefined error', () => {
    expect(getAuthErrorMessage(null)).toBe('An unexpected error occurred');
    expect(getAuthErrorMessage(undefined)).toBe('An unexpected error occurred');
  });

  it('should return error message when available', () => {
    const error = { message: 'Custom error message' };
    expect(getAuthErrorMessage(error)).toBe('Custom error message');
  });

  it('should return mapped error message for known error codes', () => {
    const error = { message: 'INVALID_CREDENTIALS' };
    expect(getAuthErrorMessage(error)).toBe(AUTH_ERROR_MESSAGES.INVALID_CREDENTIALS);
  });

  it('should handle axios error response', () => {
    const error = {
      response: {
        data: {
          message: 'Server error message',
        },
      },
    };
    expect(getAuthErrorMessage(error)).toBe('Server error message');
  });

  it('should handle error with error code in response', () => {
    const error = {
      response: {
        data: {
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User not found',
          },
        },
      },
    };
    expect(getAuthErrorMessage(error)).toBe(AUTH_ERROR_MESSAGES.USER_NOT_FOUND);
  });
});

describe('validatePasswordStrength', () => {
  it('should return invalid for empty password', () => {
    const result = validatePasswordStrength('');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password is required');
  });

  it('should return invalid for short password', () => {
    const result = validatePasswordStrength('short');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password must be at least 8 characters long');
  });

  it('should return invalid for password without lowercase', () => {
    const result = validatePasswordStrength('PASSWORD123!');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password must contain at least one lowercase letter');
  });

  it('should return invalid for password without uppercase', () => {
    const result = validatePasswordStrength('password123!');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password must contain at least one uppercase letter');
  });

  it('should return invalid for password without number', () => {
    const result = validatePasswordStrength('Password!');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password must contain at least one number');
  });

  it('should return invalid for password without special character', () => {
    const result = validatePasswordStrength('Password123');
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Password must contain at least one special character');
  });

  it('should return valid for strong password', () => {
    const result = validatePasswordStrength('Password123!');
    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });
});

describe('validateEmail', () => {
  it('should return true for valid email', () => {
    expect(validateEmail('test@example.com')).toBe(true);
    expect(validateEmail('user.name+tag@domain.co.uk')).toBe(true);
  });

  it('should return false for invalid email', () => {
    expect(validateEmail('invalid-email')).toBe(false);
    expect(validateEmail('test@')).toBe(false);
    expect(validateEmail('@example.com')).toBe(false);
    expect(validateEmail('test.example.com')).toBe(false);
  });
});

describe('validatePhoneNumber', () => {
  it('should return true for valid phone numbers', () => {
    expect(validatePhoneNumber('1234567890')).toBe(true);
    expect(validatePhoneNumber('+1 (234) 567-8900')).toBe(true);
    expect(validatePhoneNumber('234-567-8900')).toBe(true);
  });

  it('should return false for invalid phone numbers', () => {
    expect(validatePhoneNumber('123')).toBe(false);
    expect(validatePhoneNumber('abc')).toBe(false);
    expect(validatePhoneNumber('')).toBe(false);
  });
});

describe('formatPhoneNumber', () => {
  it('should format 10-digit phone number', () => {
    expect(formatPhoneNumber('1234567890')).toBe('(123) 456-7890');
  });

  it('should format 11-digit phone number with country code', () => {
    expect(formatPhoneNumber('11234567890')).toBe('+1 (123) 456-7890');
  });

  it('should return original for other formats', () => {
    expect(formatPhoneNumber('123')).toBe('123');
    expect(formatPhoneNumber('+44 123 456 7890')).toBe('+44 123 456 7890');
  });
});

describe('isTokenExpired', () => {
  it('should return true for null/undefined token', () => {
    expect(isTokenExpired(null)).toBe(true);
    expect(isTokenExpired(undefined)).toBe(true);
  });

  it('should return true for invalid token', () => {
    expect(isTokenExpired('invalid-token')).toBe(true);
  });

  it('should return true for expired token', () => {
    // Create a token that expired 1 hour ago
    const expiredTime = Math.floor(Date.now() / 1000) - 3600;
    const payload = { exp: expiredTime };
    const token = `header.${btoa(JSON.stringify(payload))}.signature`;
    
    expect(isTokenExpired(token)).toBe(true);
  });

  it('should return false for valid token', () => {
    // Create a token that expires in 1 hour
    const futureTime = Math.floor(Date.now() / 1000) + 3600;
    const payload = { exp: futureTime };
    const token = `header.${btoa(JSON.stringify(payload))}.signature`;
    
    expect(isTokenExpired(token)).toBe(false);
  });
});

describe('getUserRoleFromToken', () => {
  it('should return null for null/undefined token', () => {
    expect(getUserRoleFromToken(null)).toBe(null);
    expect(getUserRoleFromToken(undefined)).toBe(null);
  });

  it('should return null for invalid token', () => {
    expect(getUserRoleFromToken('invalid-token')).toBe(null);
  });

  it('should return role from valid token', () => {
    const payload = { role: 'admin' };
    const token = `header.${btoa(JSON.stringify(payload))}.signature`;
    
    expect(getUserRoleFromToken(token)).toBe('admin');
  });

  it('should return null if role not in token', () => {
    const payload = { user: 'test' };
    const token = `header.${btoa(JSON.stringify(payload))}.signature`;
    
    expect(getUserRoleFromToken(token)).toBe(null);
  });
});

describe('generateSecurePassword', () => {
  it('should generate password of specified length', () => {
    const password = generateSecurePassword(16);
    expect(password).toHaveLength(16);
  });

  it('should generate password with default length', () => {
    const password = generateSecurePassword();
    expect(password).toHaveLength(12);
  });

  it('should generate password with required character types', () => {
    const password = generateSecurePassword(20);
    
    expect(/[a-z]/.test(password)).toBe(true); // lowercase
    expect(/[A-Z]/.test(password)).toBe(true); // uppercase
    expect(/\d/.test(password)).toBe(true); // number
    expect(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)).toBe(true); // special
  });
});

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should delay function execution', () => {
    const mockFn = vi.fn();
    const debouncedFn = debounce(mockFn, 100);

    debouncedFn('test');
    expect(mockFn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100);
    expect(mockFn).toHaveBeenCalledWith('test');
  });

  it('should cancel previous calls', () => {
    const mockFn = vi.fn();
    const debouncedFn = debounce(mockFn, 100);

    debouncedFn('first');
    debouncedFn('second');
    
    vi.advanceTimersByTime(100);
    
    expect(mockFn).toHaveBeenCalledTimes(1);
    expect(mockFn).toHaveBeenCalledWith('second');
  });
});

describe('authStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should store and retrieve data', () => {
    const testData = { user: 'test', role: 'admin' };
    
    authStorage.setItem('user', testData);
    const retrieved = authStorage.getItem('user');
    
    expect(retrieved).toEqual(testData);
  });

  it('should return null for non-existent key', () => {
    expect(authStorage.getItem('nonexistent')).toBe(null);
  });

  it('should remove data', () => {
    authStorage.setItem('test', 'value');
    authStorage.removeItem('test');
    
    expect(authStorage.getItem('test')).toBe(null);
  });

  it('should clear all auth data', () => {
    authStorage.setItem('user', 'test');
    authStorage.setItem('token', 'abc123');
    localStorage.setItem('other_data', 'should_remain');
    
    authStorage.clear();
    
    expect(authStorage.getItem('user')).toBe(null);
    expect(authStorage.getItem('token')).toBe(null);
    expect(localStorage.getItem('other_data')).toBe('should_remain');
  });


});
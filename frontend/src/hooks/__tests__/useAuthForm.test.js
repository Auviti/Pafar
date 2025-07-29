import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useAuthForm, useLoginForm, useRegisterForm, usePasswordResetForm, useEmailVerification } from '../useAuthForm';

// Mock the AuthContext
const mockAuth = {
  login: vi.fn(),
  register: vi.fn(),
  resetPassword: vi.fn(),
  confirmResetPassword: vi.fn(),
  verifyEmail: vi.fn(),
  authService: {
    resendVerification: vi.fn(),
  },
  isLoading: false,
  error: null,
};

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuth,
}));

describe('useAuthForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return auth context properties', () => {
    const { result } = renderHook(() => useAuthForm());

    expect(result.current.login).toBe(mockAuth.login);
    expect(result.current.register).toBe(mockAuth.register);
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.formError).toBe(null);
  });

  it('should handle successful form submission', async () => {
    const onSuccess = vi.fn();
    const mockAuthFunction = vi.fn().mockResolvedValue({ success: true });
    
    const { result } = renderHook(() => useAuthForm({ onSuccess }));

    await act(async () => {
      await result.current.handleSubmit(mockAuthFunction, { test: 'data' });
    });

    expect(mockAuthFunction).toHaveBeenCalledWith({ test: 'data' });
    expect(onSuccess).toHaveBeenCalledWith({ success: true });
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.formError).toBe(null);
  });

  it('should handle form submission error', async () => {
    const onError = vi.fn();
    const mockAuthFunction = vi.fn().mockRejectedValue(new Error('Test error'));
    
    const { result } = renderHook(() => useAuthForm({ onError }));

    await act(async () => {
      try {
        await result.current.handleSubmit(mockAuthFunction, { test: 'data' });
      } catch (error) {
        // Expected to throw
      }
    });

    expect(mockAuthFunction).toHaveBeenCalledWith({ test: 'data' });
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.formError).toBe('Test error');
  });

  it('should set isSubmitting during form submission', async () => {
    const mockAuthFunction = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );
    
    const { result } = renderHook(() => useAuthForm());

    act(() => {
      result.current.handleSubmit(mockAuthFunction, { test: 'data' });
    });

    expect(result.current.isSubmitting).toBe(true);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 150));
    });

    expect(result.current.isSubmitting).toBe(false);
  });

  it('should clear error', () => {
    const { result } = renderHook(() => useAuthForm());

    act(() => {
      result.current.clearError();
    });

    expect(result.current.formError).toBe(null);
  });
});

describe('useLoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call login with credentials', async () => {
    mockAuth.login.mockResolvedValue({ access_token: 'token' });
    const { result } = renderHook(() => useLoginForm());

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password' });
    });

    expect(mockAuth.login).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password' });
  });
});

describe('useRegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call register with user data', async () => {
    mockAuth.register.mockResolvedValue({ message: 'Registration successful' });
    const { result } = renderHook(() => useRegisterForm());

    const userData = {
      first_name: 'John',
      last_name: 'Doe',
      email: 'john@example.com',
      password: 'password123',
    };

    await act(async () => {
      await result.current.register(userData);
    });

    expect(mockAuth.register).toHaveBeenCalledWith(userData);
  });
});

describe('usePasswordResetForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call resetPassword with email', async () => {
    mockAuth.resetPassword.mockResolvedValue({ message: 'Reset email sent' });
    const { result } = renderHook(() => usePasswordResetForm());

    await act(async () => {
      await result.current.resetPassword('test@example.com');
    });

    expect(mockAuth.resetPassword).toHaveBeenCalledWith('test@example.com');
  });

  it('should call confirmResetPassword with token and password', async () => {
    mockAuth.confirmResetPassword.mockResolvedValue({ message: 'Password reset successful' });
    const { result } = renderHook(() => usePasswordResetForm());

    await act(async () => {
      await result.current.confirmResetPassword('123456', 'newPassword123');
    });

    expect(mockAuth.confirmResetPassword).toHaveBeenCalledWith('123456', 'newPassword123');
  });
});

describe('useEmailVerification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call verifyEmail with token', async () => {
    mockAuth.verifyEmail.mockResolvedValue({ message: 'Email verified' });
    const { result } = renderHook(() => useEmailVerification());

    await act(async () => {
      await result.current.verifyEmail('verification-token');
    });

    expect(mockAuth.verifyEmail).toHaveBeenCalledWith('verification-token');
  });

  it('should call resendVerification with email', async () => {
    mockAuth.authService.resendVerification.mockResolvedValue({ message: 'Verification email sent' });
    const { result } = renderHook(() => useEmailVerification());

    await act(async () => {
      await result.current.resendVerification('test@example.com');
    });

    expect(mockAuth.authService.resendVerification).toHaveBeenCalledWith('test@example.com');
  });
});
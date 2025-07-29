import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';
import { AuthProvider, useAuth } from '../AuthContext';
import * as authService from '../../services/auth';

// Mock the auth service
vi.mock('../../services/auth', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    resetPassword: vi.fn(),
    confirmResetPassword: vi.fn(),
    verifyEmail: vi.fn(),
    refreshToken: vi.fn(),
  },
}));

// Mock js-cookie
vi.mock('js-cookie', () => ({
  default: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn(),
  },
}));

// Test component to access auth context
const TestComponent = () => {
  const auth = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{auth.isLoading.toString()}</div>
      <div data-testid="authenticated">{auth.isAuthenticated.toString()}</div>
      <div data-testid="user">{auth.user ? auth.user.email : 'null'}</div>
      <div data-testid="error">{auth.error || 'null'}</div>
      <button onClick={() => auth.login({ email: 'test@example.com', password: 'password' })}>
        Login
      </button>
      <button onClick={() => auth.register({ email: 'test@example.com', password: 'password' })}>
        Register
      </button>
      <button onClick={() => auth.logout()}>Logout</button>
      <button onClick={() => auth.resetPassword('test@example.com')}>Reset Password</button>
    </div>
  );
};

const renderWithAuthProvider = () => {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock Cookies.get to return null by default
    const Cookies = require('js-cookie').default;
    Cookies.get.mockReturnValue(null);
  });

  it('provides initial auth state', () => {
    renderWithAuthProvider();

    expect(screen.getByTestId('loading')).toHaveTextContent('true');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('user')).toHaveTextContent('null');
    expect(screen.getByTestId('error')).toHaveTextContent('null');
  });

  it('initializes with existing token and gets user', async () => {
    const Cookies = require('js-cookie').default;
    const mockUser = { id: '1', email: 'test@example.com' };
    
    Cookies.get.mockReturnValue('mock-token');
    authService.authService.getCurrentUser.mockResolvedValue(mockUser);

    renderWithAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
    });
  });

  it('handles login successfully', async () => {
    const mockLoginResponse = { access_token: 'token', refresh_token: 'refresh' };
    const mockUser = { id: '1', email: 'test@example.com' };
    
    authService.authService.login.mockResolvedValue(mockLoginResponse);
    authService.authService.getCurrentUser.mockResolvedValue(mockUser);

    renderWithAuthProvider();

    const loginButton = screen.getByText('Login');
    
    await act(async () => {
      loginButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
    });

    expect(authService.authService.login).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password',
    });
  });

  it('handles login failure', async () => {
    const errorMessage = 'Invalid credentials';
    authService.authService.login.mockRejectedValue(new Error(errorMessage));

    renderWithAuthProvider();

    const loginButton = screen.getByText('Login');
    
    await act(async () => {
      loginButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent(errorMessage);
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });
  });

  it('handles registration successfully', async () => {
    const mockRegisterResponse = { message: 'Registration successful' };
    authService.authService.register.mockResolvedValue(mockRegisterResponse);

    renderWithAuthProvider();

    const registerButton = screen.getByText('Register');
    
    await act(async () => {
      registerButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(authService.authService.register).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password',
    });
  });

  it('handles logout', async () => {
    const Cookies = require('js-cookie').default;
    
    // Start with authenticated state
    const mockUser = { id: '1', email: 'test@example.com' };
    Cookies.get.mockReturnValue('mock-token');
    authService.authService.getCurrentUser.mockResolvedValue(mockUser);

    renderWithAuthProvider();

    // Wait for initial auth
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    const logoutButton = screen.getByText('Logout');
    
    await act(async () => {
      logoutButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('user')).toHaveTextContent('null');
    });

    expect(authService.authService.logout).toHaveBeenCalled();
    expect(Cookies.remove).toHaveBeenCalledWith('access_token');
    expect(Cookies.remove).toHaveBeenCalledWith('refresh_token');
  });

  it('handles password reset', async () => {
    const mockResetResponse = { message: 'Reset email sent' };
    authService.authService.resetPassword.mockResolvedValue(mockResetResponse);

    renderWithAuthProvider();

    const resetButton = screen.getByText('Reset Password');
    
    await act(async () => {
      resetButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(authService.authService.resetPassword).toHaveBeenCalledWith('test@example.com');
  });

  it('throws error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });

  it('handles token initialization failure', async () => {
    const Cookies = require('js-cookie').default;
    
    Cookies.get.mockReturnValue('invalid-token');
    authService.authService.getCurrentUser.mockRejectedValue(new Error('Token expired'));

    renderWithAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('error')).toHaveTextContent('Session expired');
    });

    expect(Cookies.remove).toHaveBeenCalledWith('access_token');
    expect(Cookies.remove).toHaveBeenCalledWith('refresh_token');
  });
});
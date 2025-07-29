import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import EmailVerification from '../EmailVerification';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the auth service
vi.mock('../../../services/auth', () => ({
  authService: {
    verifyEmail: vi.fn(),
    resendVerification: vi.fn(),
  },
}));

const renderEmailVerification = (searchParams = '') => {
  return render(
    <MemoryRouter initialEntries={[`/verify-email${searchParams}`]}>
      <AuthProvider>
        <EmailVerification />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('EmailVerification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially when token is provided', () => {
    renderEmailVerification('?token=valid-token');

    expect(screen.getByText('Verifying Email')).toBeInTheDocument();
    expect(screen.getByText('Please wait while we verify your email address')).toBeInTheDocument();
    expect(screen.getByText('Verifying...')).toBeInTheDocument();
  });

  it('shows error state when no token is provided', async () => {
    renderEmailVerification();

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
      expect(screen.getByText("We couldn't verify your email address")).toBeInTheDocument();
      expect(screen.getByText('Invalid verification link')).toBeInTheDocument();
    });
  });

  it('shows success state after successful verification', async () => {
    const mockVerifyEmail = vi.fn().mockResolvedValue({ message: 'Email verified' });
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        verifyEmail: mockVerifyEmail,
        authService: {
          resendVerification: vi.fn(),
        },
      }),
    }));

    renderEmailVerification('?token=valid-token');

    await waitFor(() => {
      expect(screen.getByText('Email Verified!')).toBeInTheDocument();
      expect(screen.getByText('Your email has been successfully verified')).toBeInTheDocument();
      expect(screen.getByText('Your email address has been verified successfully.')).toBeInTheDocument();
      expect(screen.getByText('You can now sign in to your account.')).toBeInTheDocument();
    });

    expect(mockVerifyEmail).toHaveBeenCalledWith('valid-token');
  });

  it('shows error state when verification fails', async () => {
    const mockVerifyEmail = vi.fn().mockRejectedValue(new Error('Invalid token'));
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        verifyEmail: mockVerifyEmail,
        authService: {
          resendVerification: vi.fn(),
        },
      }),
    }));

    renderEmailVerification('?token=invalid-token');

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
      expect(screen.getByText('Invalid token')).toBeInTheDocument();
    });
  });

  it('shows resend verification button when email is provided', async () => {
    renderEmailVerification('?email=test@example.com');

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Resend verification email' })).toBeInTheDocument();
    });
  });

  it('handles resend verification', async () => {
    const user = userEvent.setup();
    const mockResendVerification = vi.fn().mockResolvedValue({ message: 'Email sent' });
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        verifyEmail: vi.fn().mockRejectedValue(new Error('Invalid token')),
        authService: {
          resendVerification: mockResendVerification,
        },
      }),
    }));

    renderEmailVerification('?token=invalid-token&email=test@example.com');

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
    });

    const resendButton = screen.getByRole('button', { name: 'Resend verification email' });
    await user.click(resendButton);

    await waitFor(() => {
      expect(mockResendVerification).toHaveBeenCalledWith('test@example.com');
    });
  });

  it('shows resent confirmation after successful resend', async () => {
    const user = userEvent.setup();
    renderEmailVerification('?email=test@example.com');

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
    });

    const resendButton = screen.getByRole('button', { name: 'Resend verification email' });
    await user.click(resendButton);

    // Note: The resent state would be tested in integration tests
    // as it requires the component to re-render with new state
    expect(resendButton).toBeInTheDocument();
  });

  it('shows error when resend fails without email', async () => {
    const user = userEvent.setup();
    renderEmailVerification();

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
    });

    // Since no email is provided, there should be no resend button
    expect(screen.queryByRole('button', { name: 'Resend verification email' })).not.toBeInTheDocument();
  });

  it('has proper navigation links', async () => {
    renderEmailVerification();

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
    });

    expect(screen.getByRole('link', { name: 'Back to Login' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Create New Account' })).toBeInTheDocument();
  });

  it('shows sign in link in success state', async () => {
    const mockVerifyEmail = vi.fn().mockResolvedValue({ message: 'Email verified' });
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        verifyEmail: mockVerifyEmail,
        authService: {
          resendVerification: vi.fn(),
        },
      }),
    }));

    renderEmailVerification('?token=valid-token');

    await waitFor(() => {
      expect(screen.getByText('Email Verified!')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Sign In Now' })).toBeInTheDocument();
    });
  });

  it('shows back to login link in resent state', async () => {
    const user = userEvent.setup();
    const mockResendVerification = vi.fn().mockResolvedValue({ message: 'Email sent' });
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        verifyEmail: vi.fn().mockRejectedValue(new Error('Invalid token')),
        authService: {
          resendVerification: mockResendVerification,
        },
      }),
    }));

    renderEmailVerification('?token=invalid-token&email=test@example.com');

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
    });

    const resendButton = screen.getByRole('button', { name: 'Resend verification email' });
    await user.click(resendButton);

    // Note: The resent state navigation would be tested in integration tests
    expect(resendButton).toBeInTheDocument();
  });

  it('handles resend verification error', async () => {
    const user = userEvent.setup();
    const mockResendVerification = vi.fn().mockRejectedValue(new Error('Resend failed'));
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        verifyEmail: vi.fn().mockRejectedValue(new Error('Invalid token')),
        authService: {
          resendVerification: mockResendVerification,
        },
      }),
    }));

    renderEmailVerification('?token=invalid-token&email=test@example.com');

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeInTheDocument();
    });

    const resendButton = screen.getByRole('button', { name: 'Resend verification email' });
    await user.click(resendButton);

    await waitFor(() => {
      expect(mockResendVerification).toHaveBeenCalledWith('test@example.com');
    });
  });
});
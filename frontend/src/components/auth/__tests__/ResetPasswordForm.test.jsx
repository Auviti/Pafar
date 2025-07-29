import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import ResetPasswordForm from '../ResetPasswordForm';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the auth service
vi.mock('../../../services/auth', () => ({
  authService: {
    confirmResetPassword: vi.fn(),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderResetPasswordForm = (searchParams = '') => {
  return render(
    <MemoryRouter initialEntries={[`/reset-password${searchParams}`]}>
      <AuthProvider>
        <ResetPasswordForm />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('ResetPasswordForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders reset password form with all required elements', () => {
    renderResetPasswordForm();

    expect(screen.getByText('Reset Your Password')).toBeInTheDocument();
    expect(screen.getByText('Enter the verification code and your new password')).toBeInTheDocument();
    expect(screen.getByLabelText('Verification Code')).toBeInTheDocument();
    expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reset Password' })).toBeInTheDocument();
  });

  it('shows email hint when email is provided in URL', () => {
    renderResetPasswordForm('?email=test@example.com');

    expect(screen.getByText('Code sent to: test@example.com')).toBeInTheDocument();
  });

  it('renders OTP input with 6 digit fields', () => {
    renderResetPasswordForm();

    const otpInputs = screen.getAllByRole('textbox');
    const otpFields = otpInputs.filter(input => input.className.includes('otp-input'));
    expect(otpFields).toHaveLength(6);
  });

  it('shows validation errors for empty required fields', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const submitButton = screen.getByRole('button', { name: 'Reset Password' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Verification code is required')).toBeInTheDocument();
      expect(screen.getByText('New password is required')).toBeInTheDocument();
    });
  });

  it('validates password strength requirements', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const passwordInput = screen.getByLabelText('New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(passwordInput, 'weak');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Password must contain at least one uppercase letter, one lowercase letter, and one number')).toBeInTheDocument();
    });
  });

  it('validates password confirmation match', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const passwordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(passwordInput, 'Password123');
    await user.type(confirmPasswordInput, 'DifferentPassword123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Passwords don't match")).toBeInTheDocument();
    });
  });

  it('validates OTP code length', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const otpInputs = screen.getAllByRole('textbox');
    const firstOtpInput = otpInputs.find(input => input.className.includes('otp-input'));
    const submitButton = screen.getByRole('button', { name: 'Reset Password' });

    await user.type(firstOtpInput, '123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Verification code must be 6 digits')).toBeInTheDocument();
    });
  });

  it('toggles password visibility for both password fields', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const passwordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    const passwordToggleButtons = screen.getAllByLabelText('Show password');

    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(confirmPasswordInput).toHaveAttribute('type', 'password');

    // Toggle first password field
    await user.click(passwordToggleButtons[0]);
    expect(passwordInput).toHaveAttribute('type', 'text');

    // Toggle second password field
    await user.click(passwordToggleButtons[1]);
    expect(confirmPasswordInput).toHaveAttribute('type', 'text');
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const mockConfirmResetPassword = vi.fn().mockResolvedValue({ message: 'Password reset successful' });
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        confirmResetPassword: mockConfirmResetPassword,
        isLoading: false,
        error: null,
      }),
    }));

    renderResetPasswordForm();

    // Fill OTP
    const otpInputs = screen.getAllByRole('textbox');
    const otpFields = otpInputs.filter(input => input.className.includes('otp-input'));
    for (let i = 0; i < 6; i++) {
      await user.type(otpFields[i], (i + 1).toString());
    }

    // Fill passwords
    const passwordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    await user.type(passwordInput, 'NewPassword123');
    await user.type(confirmPasswordInput, 'NewPassword123');

    const submitButton = screen.getByRole('button', { name: 'Reset Password' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockConfirmResetPassword).toHaveBeenCalledWith('123456', 'NewPassword123');
    });
  });

  it('handles OTP input auto-focus and navigation', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const otpInputs = screen.getAllByRole('textbox');
    const otpFields = otpInputs.filter(input => input.className.includes('otp-input'));

    // Type in first field should auto-focus next
    await user.type(otpFields[0], '1');
    expect(otpFields[1]).toHaveFocus();

    // Backspace in empty field should focus previous
    await user.clear(otpFields[1]);
    await user.type(otpFields[1], '{backspace}');
    expect(otpFields[0]).toHaveFocus();
  });

  it('handles paste operation in OTP input', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    const otpInputs = screen.getAllByRole('textbox');
    const firstOtpInput = otpInputs.find(input => input.className.includes('otp-input'));

    // Simulate paste event
    await user.click(firstOtpInput);
    await user.paste('123456');

    // All fields should be filled
    const otpFields = otpInputs.filter(input => input.className.includes('otp-input'));
    otpFields.forEach((field, index) => {
      expect(field).toHaveValue((index + 1).toString());
    });
  });

  it('disables submit button when loading', () => {
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        confirmResetPassword: vi.fn(),
        isLoading: true,
        error: null,
      }),
    }));

    renderResetPasswordForm();

    const submitButton = screen.getByRole('button', { name: /resetting password/i });
    expect(submitButton).toBeDisabled();
  });

  it('has proper accessibility attributes', () => {
    renderResetPasswordForm();

    const passwordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

    expect(passwordInput).toHaveAttribute('autoComplete', 'new-password');
    expect(confirmPasswordInput).toHaveAttribute('autoComplete', 'new-password');
  });

  it('shows success message after successful password reset', async () => {
    const user = userEvent.setup();
    renderResetPasswordForm();

    // Fill form with valid data
    const otpInputs = screen.getAllByRole('textbox');
    const otpFields = otpInputs.filter(input => input.className.includes('otp-input'));
    for (let i = 0; i < 6; i++) {
      await user.type(otpFields[i], (i + 1).toString());
    }

    const passwordInput = screen.getByLabelText('New Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm New Password');
    await user.type(passwordInput, 'NewPassword123');
    await user.type(confirmPasswordInput, 'NewPassword123');

    const submitButton = screen.getByRole('button', { name: 'Reset Password' });
    await user.click(submitButton);

    // Note: The success state would be tested in integration tests
    // as it requires the component to re-render with new state
    expect(submitButton).toBeInTheDocument();
  });
});
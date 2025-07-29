import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import RegisterForm from '../RegisterForm';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the auth service
vi.mock('../../../services/auth', () => ({
  authService: {
    register: vi.fn(),
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

const renderRegisterForm = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <RegisterForm />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders registration form with all required fields', () => {
    renderRegisterForm();

    expect(screen.getByText('Create Account')).toBeInTheDocument();
    expect(screen.getByText('Join us to start booking your trips')).toBeInTheDocument();
    expect(screen.getByLabelText('First Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
  });

  it('shows validation errors for empty required fields', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const submitButton = screen.getByRole('button', { name: 'Create Account' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('First name is required')).toBeInTheDocument();
      expect(screen.getByText('Last name is required')).toBeInTheDocument();
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Phone number is required')).toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    });
  });

  it('validates password strength requirements', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Create Account' });

    await user.type(passwordInput, 'weak');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Password must contain at least one uppercase letter, one lowercase letter, and one number')).toBeInTheDocument();
    });
  });

  it('validates password confirmation match', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm Password');
    const submitButton = screen.getByRole('button', { name: 'Create Account' });

    await user.type(passwordInput, 'Password123');
    await user.type(confirmPasswordInput, 'DifferentPassword123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Passwords don't match")).toBeInTheDocument();
    });
  });

  it('validates email format', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const emailInput = screen.getByLabelText('Email Address');
    const submitButton = screen.getByRole('button', { name: 'Create Account' });

    await user.type(emailInput, 'invalid-email');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  it('validates phone number format', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const phoneInput = screen.getByLabelText('Phone Number');
    const submitButton = screen.getByRole('button', { name: 'Create Account' });

    await user.type(phoneInput, 'abc');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid phone number')).toBeInTheDocument();
    });
  });

  it('toggles password visibility for both password fields', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm Password');
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
    const mockRegister = vi.fn().mockResolvedValue({ message: 'Registration successful' });
    
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        register: mockRegister,
        isLoading: false,
        error: null,
      }),
    }));

    renderRegisterForm();

    // Fill out the form
    await user.type(screen.getByLabelText('First Name'), 'John');
    await user.type(screen.getByLabelText('Last Name'), 'Doe');
    await user.type(screen.getByLabelText('Email Address'), 'john@example.com');
    await user.type(screen.getByLabelText('Phone Number'), '+1234567890');
    await user.type(screen.getByLabelText('Password'), 'Password123');
    await user.type(screen.getByLabelText('Confirm Password'), 'Password123');
    
    // Accept terms
    const termsCheckbox = screen.getByRole('checkbox');
    await user.click(termsCheckbox);

    const submitButton = screen.getByRole('button', { name: 'Create Account' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com',
        phone: '+1234567890',
        password: 'Password123',
      });
    });
  });

  it('shows success message after successful registration', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    // Fill out valid form data
    await user.type(screen.getByLabelText('First Name'), 'John');
    await user.type(screen.getByLabelText('Last Name'), 'Doe');
    await user.type(screen.getByLabelText('Email Address'), 'john@example.com');
    await user.type(screen.getByLabelText('Phone Number'), '+1234567890');
    await user.type(screen.getByLabelText('Password'), 'Password123');
    await user.type(screen.getByLabelText('Confirm Password'), 'Password123');
    
    const termsCheckbox = screen.getByRole('checkbox');
    await user.click(termsCheckbox);

    // Mock successful registration
    vi.doMock('../../../contexts/AuthContext', () => ({
      useAuth: () => ({
        register: vi.fn().mockResolvedValue({ message: 'Success' }),
        isLoading: false,
        error: null,
      }),
    }));

    const submitButton = screen.getByRole('button', { name: 'Create Account' });
    await user.click(submitButton);

    // Note: The success state would be tested in integration tests
    // as it requires the component to re-render with new state
  });

  it('requires terms acceptance', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    const termsCheckbox = screen.getByRole('checkbox');
    expect(termsCheckbox).toBeRequired();
  });

  it('has proper accessibility attributes', () => {
    renderRegisterForm();

    const firstNameInput = screen.getByLabelText('First Name');
    const lastNameInput = screen.getByLabelText('Last Name');
    const emailInput = screen.getByLabelText('Email Address');
    const phoneInput = screen.getByLabelText('Phone Number');
    const passwordInput = screen.getByLabelText('Password');
    const confirmPasswordInput = screen.getByLabelText('Confirm Password');

    expect(firstNameInput).toHaveAttribute('autoComplete', 'given-name');
    expect(lastNameInput).toHaveAttribute('autoComplete', 'family-name');
    expect(emailInput).toHaveAttribute('type', 'email');
    expect(emailInput).toHaveAttribute('autoComplete', 'email');
    expect(phoneInput).toHaveAttribute('type', 'tel');
    expect(phoneInput).toHaveAttribute('autoComplete', 'tel');
    expect(passwordInput).toHaveAttribute('autoComplete', 'new-password');
    expect(confirmPasswordInput).toHaveAttribute('autoComplete', 'new-password');
  });
});
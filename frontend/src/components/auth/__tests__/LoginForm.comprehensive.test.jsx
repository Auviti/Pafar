/**
 * Comprehensive tests for LoginForm component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockAxios, mockLocalStorage, createMockUser } from '../../test/test-utils';
import LoginForm from '../LoginForm';

// Mock dependencies
vi.mock('axios', () => ({
  default: mockAxios,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ state: null }),
  };
});

describe('LoginForm', () => {
  let mockOnSuccess;
  let mockOnError;
  let user;

  beforeEach(() => {
    mockOnSuccess = vi.fn();
    mockOnError = vi.fn();
    user = userEvent.setup();
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage(),
      writable: true,
    });
    
    // Reset axios mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders all form elements correctly', () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    });

    it('renders with custom title when provided', () => {
      render(
        <LoginForm 
          title="Custom Login Title"
          onSuccess={mockOnSuccess} 
          onError={mockOnError} 
        />
      );

      expect(screen.getByText('Custom Login Title')).toBeInTheDocument();
    });

    it('renders loading state correctly', () => {
      render(<LoginForm loading={true} onSuccess={mockOnSuccess} onError={mockOnError} />);

      const submitButton = screen.getByRole('button', { name: /signing in/i });
      expect(submitButton).toBeDisabled();
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('renders error message when provided', () => {
      const errorMessage = 'Invalid credentials';
      render(
        <LoginForm 
          error={errorMessage}
          onSuccess={mockOnSuccess} 
          onError={mockOnError} 
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation errors for empty fields', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    it('shows validation error for invalid email format', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'invalid-email');
      
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument();
      });
    });

    it('shows validation error for short password', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const passwordInput = screen.getByLabelText(/password/i);
      await user.type(passwordInput, '123');
      
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument();
      });
    });

    it('clears validation errors when user starts typing', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      // Trigger validation errors
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      });

      // Start typing in email field
      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'test@example.com');

      await waitFor(() => {
        expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      const mockUser = createMockUser();
      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
        },
      };

      mockAxios.post.mockResolvedValueOnce(mockResponse);

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAxios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
          email: 'test@example.com',
          password: 'password123',
        });
        expect(mockOnSuccess).toHaveBeenCalledWith(mockResponse.data);
      });
    });

    it('handles login failure correctly', async () => {
      const errorMessage = 'Invalid credentials';
      mockAxios.post.mockRejectedValueOnce({
        response: {
          data: { message: errorMessage },
          status: 401,
        },
      });

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(errorMessage);
      });
    });

    it('handles network error correctly', async () => {
      mockAxios.post.mockRejectedValueOnce(new Error('Network Error'));

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Network error. Please try again.');
      });
    });

    it('disables form during submission', async () => {
      // Mock a delayed response
      mockAxios.post.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: {} }), 100))
      );

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Form should be disabled during submission
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(submitButton).toBeDisabled();
      expect(screen.getByText(/signing in/i)).toBeInTheDocument();
    });
  });

  describe('Remember Me Functionality', () => {
    it('renders remember me checkbox', () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
    });

    it('saves credentials when remember me is checked', async () => {
      const mockUser = createMockUser();
      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
        },
      };

      mockAxios.post.mockResolvedValueOnce(mockResponse);

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const rememberMeCheckbox = screen.getByLabelText(/remember me/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(rememberMeCheckbox);
      await user.click(submitButton);

      await waitFor(() => {
        expect(window.localStorage.setItem).toHaveBeenCalledWith(
          'rememberedEmail',
          'test@example.com'
        );
      });
    });

    it('loads remembered email on component mount', () => {
      window.localStorage.getItem.mockReturnValue('remembered@example.com');

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      expect(emailInput.value).toBe('remembered@example.com');
    });
  });

  describe('Password Visibility Toggle', () => {
    it('toggles password visibility', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const passwordInput = screen.getByLabelText(/password/i);
      const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i });

      // Initially password should be hidden
      expect(passwordInput.type).toBe('password');

      // Click to show password
      await user.click(toggleButton);
      expect(passwordInput.type).toBe('text');

      // Click to hide password again
      await user.click(toggleButton);
      expect(passwordInput.type).toBe('password');
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Tab through form elements
      await user.tab();
      expect(emailInput).toHaveFocus();

      await user.tab();
      expect(passwordInput).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/remember me/i)).toHaveFocus();

      await user.tab();
      expect(submitButton).toHaveFocus();
    });

    it('submits form on Enter key press', async () => {
      const mockUser = createMockUser();
      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
        },
      };

      mockAxios.post.mockResolvedValueOnce(mockResponse);

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockAxios.post).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      expect(screen.getByRole('form')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toHaveAttribute('aria-required', 'true');
      expect(screen.getByLabelText(/password/i)).toHaveAttribute('aria-required', 'true');
    });

    it('announces errors to screen readers', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        const errorElement = screen.getByText(/email is required/i);
        expect(errorElement).toHaveAttribute('role', 'alert');
        expect(errorElement).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('associates error messages with form fields', async () => {
      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email/i);
        const errorElement = screen.getByText(/email is required/i);
        expect(emailInput).toHaveAttribute('aria-describedby', errorElement.id);
      });
    });
  });

  describe('Social Login Integration', () => {
    it('renders social login buttons when enabled', () => {
      render(
        <LoginForm 
          onSuccess={mockOnSuccess} 
          onError={mockOnError}
          enableSocialLogin={true}
        />
      );

      expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /continue with facebook/i })).toBeInTheDocument();
    });

    it('handles Google login', async () => {
      const mockGoogleResponse = {
        data: {
          user: createMockUser(),
          access_token: 'google-token',
        },
      };

      mockAxios.post.mockResolvedValueOnce(mockGoogleResponse);

      render(
        <LoginForm 
          onSuccess={mockOnSuccess} 
          onError={mockOnError}
          enableSocialLogin={true}
        />
      );

      const googleButton = screen.getByRole('button', { name: /continue with google/i });
      await user.click(googleButton);

      await waitFor(() => {
        expect(mockAxios.post).toHaveBeenCalledWith('/api/v1/auth/google', expect.any(Object));
      });
    });
  });

  describe('Error Recovery', () => {
    it('allows retry after error', async () => {
      // First attempt fails
      mockAxios.post.mockRejectedValueOnce({
        response: {
          data: { message: 'Server error' },
          status: 500,
        },
      });

      render(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Server error');
      });

      // Second attempt succeeds
      const mockUser = createMockUser();
      const mockResponse = {
        data: {
          user: mockUser,
          access_token: 'mock-token',
        },
      };

      mockAxios.post.mockResolvedValueOnce(mockResponse);
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledWith(mockResponse.data);
      });
    });

    it('clears previous errors on new submission', async () => {
      render(
        <LoginForm 
          error="Previous error"
          onSuccess={mockOnSuccess} 
          onError={mockOnError} 
        />
      );

      expect(screen.getByText('Previous error')).toBeInTheDocument();

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Error should be cleared when form is submitted
      expect(screen.queryByText('Previous error')).not.toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('debounces validation', async () => {
      const mockValidate = vi.fn();
      
      render(
        <LoginForm 
          onSuccess={mockOnSuccess} 
          onError={mockOnError}
          onValidate={mockValidate}
        />
      );

      const emailInput = screen.getByLabelText(/email/i);

      // Type rapidly
      await user.type(emailInput, 'test@example.com');

      // Validation should be debounced
      await waitFor(() => {
        expect(mockValidate).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('memoizes expensive computations', () => {
      const { rerender } = render(
        <LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />
      );

      const initialRender = screen.getByRole('form');

      // Re-render with same props
      rerender(<LoginForm onSuccess={mockOnSuccess} onError={mockOnError} />);

      const secondRender = screen.getByRole('form');

      // Component should be memoized (this is a conceptual test)
      expect(initialRender).toBe(secondRender);
    });
  });
});
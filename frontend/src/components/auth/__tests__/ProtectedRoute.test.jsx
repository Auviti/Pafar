import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import ProtectedRoute, { PublicRoute, withAuth } from '../ProtectedRoute';

// Mock the useAuth hook
const mockUseAuth = vi.fn();
vi.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

const TestComponent = () => <div>Protected Content</div>;
const TestComponentWithAuth = withAuth(TestComponent);

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner when authentication is loading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    });

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </MemoryRouter>
    );

    // The component should not render the protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders protected content when user is authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', role: 'passenger' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('shows access denied when user lacks required role', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', role: 'passenger' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRole="admin">
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText("You don't have permission to access this page.")).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders content when user has required role', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', role: 'admin' },
    });

    render(
      <BrowserRouter>
        <ProtectedRoute requiredRole="admin">
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('renders custom fallback when loading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
    });

    const CustomFallback = () => <div>Custom Loading...</div>;

    render(
      <BrowserRouter>
        <ProtectedRoute fallback={<CustomFallback />}>
          <TestComponent />
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Custom Loading...')).toBeInTheDocument();
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });
});

describe('PublicRoute', () => {
  it('renders content when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    });

    render(
      <BrowserRouter>
        <PublicRoute>
          <div>Public Content</div>
        </PublicRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Public Content')).toBeInTheDocument();
  });

  it('shows loading when authentication is loading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
    });

    render(
      <BrowserRouter>
        <PublicRoute>
          <div>Public Content</div>
        </PublicRoute>
      </BrowserRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.queryByText('Public Content')).not.toBeInTheDocument();
  });

  it('redirects authenticated users away from public routes', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', role: 'passenger' },
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <PublicRoute>
          <div>Login Form</div>
        </PublicRoute>
      </MemoryRouter>
    );

    // The component should not render the public content
    expect(screen.queryByText('Login Form')).not.toBeInTheDocument();
  });
});

describe('withAuth HOC', () => {
  it('wraps component with authentication protection', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', role: 'passenger' },
    });

    render(
      <BrowserRouter>
        <TestComponentWithAuth />
      </BrowserRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('applies role-based protection when specified', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: '1', role: 'passenger' },
    });

    const AdminComponent = withAuth(TestComponent, 'admin');

    render(
      <BrowserRouter>
        <AdminComponent />
      </BrowserRouter>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});
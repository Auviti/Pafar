import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import UserManagement from '../UserManagement';
import { adminService } from '../../../services/admin';

// Mock the admin service
vi.mock('../../../services/admin', () => ({
  adminService: {
    getUsers: vi.fn(),
    updateUserStatus: vi.fn(),
    suspendUser: vi.fn(),
  },
}));

// Mock window.prompt
global.prompt = vi.fn();

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithQueryClient = (component) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

const mockUsersData = {
  users: [
    {
      id: '1',
      first_name: 'John',
      last_name: 'Doe',
      email: 'john@example.com',
      phone: '+1234567890',
      role: 'passenger',
      status: 'active',
      is_verified: true,
      created_at: '2024-01-01T00:00:00Z',
      last_login: '2024-01-15T10:00:00Z',
      total_bookings: 5,
      total_spent: 250,
      avg_rating: 4.5,
    },
    {
      id: '2',
      first_name: 'Jane',
      last_name: 'Smith',
      email: 'jane@example.com',
      phone: null,
      role: 'driver',
      status: 'inactive',
      is_verified: false,
      created_at: '2024-01-02T00:00:00Z',
      last_login: null,
      total_bookings: 0,
      total_spent: 0,
      avg_rating: null,
    },
  ],
  total_pages: 1,
};

describe('UserManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    adminService.getUsers.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithQueryClient(<UserManagement />);

    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  it('renders user management interface when data loads', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Check header elements
    expect(screen.getByText('Export Users')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search users by name or email...')).toBeInTheDocument();

    // Check filter dropdowns
    expect(screen.getByDisplayValue('All Roles')).toBeInTheDocument();
    expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
  });

  it('displays users in table format', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Role')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('Joined')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();

    // Check user data
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('passenger')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getAllByText('✅')).toHaveLength(1);
    expect(screen.getAllByText('❌')).toHaveLength(1);
  });

  it('handles search functionality', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search users by name or email...')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search users by name or email...');
    fireEvent.change(searchInput, { target: { value: 'john' } });

    expect(searchInput.value).toBe('john');
  });

  it('handles role filter changes', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('All Roles')).toBeInTheDocument();
    });

    const roleFilter = screen.getByDisplayValue('All Roles');
    fireEvent.change(roleFilter, { target: { value: 'passenger' } });

    expect(roleFilter.value).toBe('passenger');
  });

  it('handles status filter changes', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
    });

    const statusFilter = screen.getByDisplayValue('All Status');
    fireEvent.change(statusFilter, { target: { value: 'active' } });

    expect(statusFilter.value).toBe('active');
  });

  it('opens user modal when view button is clicked', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('View')).toHaveLength(2);
    });

    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[0]);

    // Check if modal opens
    await waitFor(() => {
      expect(screen.getByText('User Details')).toBeInTheDocument();
    });

    // Check user details in modal (use getAllByText since name appears in both table and modal)
    expect(screen.getAllByText('John Doe')).toHaveLength(2);
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('+1234567890')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument(); // Total bookings
    expect(screen.getByText('$250')).toBeInTheDocument(); // Total spent
    expect(screen.getByText('4.5')).toBeInTheDocument(); // Avg rating
  });

  it('handles user activation', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);
    adminService.updateUserStatus.mockResolvedValue({ success: true });

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('Activate')).toHaveLength(2);
    });

    const activateButtons = screen.getAllByText('Activate');
    fireEvent.click(activateButtons[1]); // Click on Jane's activate button

    await waitFor(() => {
      expect(adminService.updateUserStatus).toHaveBeenCalledWith('2', 'active');
    });
  });

  it('handles user suspension with reason', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);
    adminService.suspendUser.mockResolvedValue({ success: true });
    global.prompt.mockReturnValue('Violation of terms');

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('Suspend')).toHaveLength(2);
    });

    const suspendButtons = screen.getAllByText('Suspend');
    fireEvent.click(suspendButtons[0]);

    expect(global.prompt).toHaveBeenCalledWith('Enter suspension reason:');

    await waitFor(() => {
      expect(adminService.suspendUser).toHaveBeenCalledWith('1', 'Violation of terms');
    });
  });

  it('does not suspend user if no reason provided', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);
    global.prompt.mockReturnValue(null); // User cancels prompt

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('Suspend')).toHaveLength(2);
    });

    const suspendButtons = screen.getAllByText('Suspend');
    fireEvent.click(suspendButtons[0]);

    expect(global.prompt).toHaveBeenCalled();
    expect(adminService.suspendUser).not.toHaveBeenCalled();
  });

  it('renders pagination controls', async () => {
    const paginatedData = { ...mockUsersData, total_pages: 3 };
    adminService.getUsers.mockResolvedValue(paginatedData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });
  });

  it('handles pagination navigation', async () => {
    const paginatedData = { ...mockUsersData, total_pages: 3 };
    adminService.getUsers.mockResolvedValue(paginatedData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    // Should update the page state (we can't easily test the API call without more complex mocking)
    // Just verify the button still exists after clicking
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('closes modal when close button is clicked', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('View')).toHaveLength(2);
    });

    // Open modal
    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('User Details')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText('User Details')).not.toBeInTheDocument();
    });
  });

  it('renders error state when API call fails', async () => {
    const errorMessage = 'Failed to fetch users';
    adminService.getUsers.mockRejectedValue(new Error(errorMessage));

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText(`Error loading users: ${errorMessage}`)).toBeInTheDocument();
    });
  });

  it('handles users with missing optional data', async () => {
    adminService.getUsers.mockResolvedValue(mockUsersData);

    renderWithQueryClient(<UserManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('View')).toHaveLength(2);
    });

    // Open modal for Jane (user with missing data)
    const viewButtons = screen.getAllByText('View');
    fireEvent.click(viewButtons[1]);

    await waitFor(() => {
      expect(screen.getByText('User Details')).toBeInTheDocument();
    });

    // Check handling of missing data
    expect(screen.getByText('Not provided')).toBeInTheDocument(); // Phone
    expect(screen.getByText('Never')).toBeInTheDocument(); // Last login
    expect(screen.getByText('N/A')).toBeInTheDocument(); // Avg rating
  });
});
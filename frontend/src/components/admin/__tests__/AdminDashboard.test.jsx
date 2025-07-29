import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import AdminDashboard from '../AdminDashboard';
import { adminService } from '../../../services/admin';

// Mock the admin service
vi.mock('../../../services/admin', () => ({
  adminService: {
    getDashboardMetrics: vi.fn(),
  },
}));

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

const mockMetrics = {
  total_bookings: 1250,
  bookings_change: 12.5,
  active_users: 850,
  users_change: 8.3,
  revenue: 45000,
  revenue_change: -2.1,
  fleet_utilization: 78,
  utilization_change: 5.2,
  booking_trend: [100, 120, 110, 130, 125],
  daily_revenue: 1500,
  live_trips: [
    {
      id: '1',
      route: 'Lagos - Abuja',
      bus_number: 'BUS-001',
      driver_name: 'John Doe',
      status: 'in_progress',
      passengers: 35,
      capacity: 40,
    },
    {
      id: '2',
      route: 'Abuja - Kano',
      bus_number: 'BUS-002',
      driver_name: 'Jane Smith',
      status: 'scheduled',
      passengers: 20,
      capacity: 40,
    },
  ],
  recent_activities: [
    {
      timestamp: '2024-01-15T10:30:00Z',
      message: 'New booking created for Lagos - Abuja route',
    },
    {
      timestamp: '2024-01-15T10:25:00Z',
      message: 'Bus BUS-001 departed from Lagos terminal',
    },
  ],
};

describe('AdminDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    adminService.getDashboardMetrics.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithQueryClient(<AdminDashboard />);

    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders dashboard with metrics when data loads successfully', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    });

    // Check metric cards
    expect(screen.getByText('Total Bookings')).toBeInTheDocument();
    expect(screen.getByText('1250')).toBeInTheDocument();
    expect(screen.getByText('↗ 12.5%')).toBeInTheDocument();

    expect(screen.getByText('Active Users')).toBeInTheDocument();
    expect(screen.getByText('850')).toBeInTheDocument();

    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('$45000')).toBeInTheDocument();
    expect(screen.getByText('↘ 2.1%')).toBeInTheDocument();

    expect(screen.getByText('Fleet Utilization')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
  });

  it('renders live trips section', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Live Trips (2)')).toBeInTheDocument();
    });

    // Check live trip cards
    expect(screen.getByText('Lagos - Abuja')).toBeInTheDocument();
    expect(screen.getByText('Bus: BUS-001')).toBeInTheDocument();
    expect(screen.getByText('Driver: John Doe')).toBeInTheDocument();
    expect(screen.getByText('35/40 passengers')).toBeInTheDocument();

    expect(screen.getByText('Abuja - Kano')).toBeInTheDocument();
    expect(screen.getByText('Bus: BUS-002')).toBeInTheDocument();
    expect(screen.getByText('Driver: Jane Smith')).toBeInTheDocument();
  });

  it('renders recent activity section', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    });

    expect(
      screen.getByText('New booking created for Lagos - Abuja route')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Bus BUS-001 departed from Lagos terminal')
    ).toBeInTheDocument();
  });

  it('renders charts section with placeholders', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Booking Trends')).toBeInTheDocument();
      expect(screen.getByText('Revenue Analysis')).toBeInTheDocument();
    });

    expect(screen.getByText('Chart visualization would go here')).toBeInTheDocument();
    expect(screen.getByText('Revenue chart would go here')).toBeInTheDocument();
    expect(screen.getByText('Daily revenue: $1500')).toBeInTheDocument();
  });

  it('renders quick actions section', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    });

    expect(screen.getByText('📊 Generate Report')).toBeInTheDocument();
    expect(screen.getByText('🚨 View Alerts')).toBeInTheDocument();
    expect(screen.getByText('📧 Send Notifications')).toBeInTheDocument();
    expect(screen.getByText('⚙️ System Settings')).toBeInTheDocument();
  });

  it('handles time range selection', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Last 7 Days')).toBeInTheDocument();
    });

    // Check that all time range options are available
    const select = screen.getByDisplayValue('Last 7 Days');
    expect(select).toBeInTheDocument();
    
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(4);
    expect(screen.getByText('Last 24 Hours')).toBeInTheDocument();
    expect(screen.getByText('Last 7 Days')).toBeInTheDocument();
    expect(screen.getByText('Last 30 Days')).toBeInTheDocument();
    expect(screen.getByText('Last 90 Days')).toBeInTheDocument();
  });

  it('renders error state when API call fails', async () => {
    const errorMessage = 'Failed to fetch dashboard metrics';
    adminService.getDashboardMetrics.mockRejectedValue(new Error(errorMessage));

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('handles empty live trips', async () => {
    const emptyMetrics = { ...mockMetrics, live_trips: [] };
    adminService.getDashboardMetrics.mockResolvedValue(emptyMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Live Trips (0)')).toBeInTheDocument();
      expect(screen.getByText('No active trips')).toBeInTheDocument();
    });
  });

  it('handles empty recent activities', async () => {
    const emptyMetrics = { ...mockMetrics, recent_activities: [] };
    adminService.getDashboardMetrics.mockResolvedValue(emptyMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('No recent activity')).toBeInTheDocument();
    });
  });

  it('displays correct status badges for trips', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      const statusBadges = screen.getAllByText(/in_progress|scheduled/);
      expect(statusBadges).toHaveLength(2);
    });
  });

  it('formats timestamps correctly in recent activities', async () => {
    adminService.getDashboardMetrics.mockResolvedValue(mockMetrics);

    renderWithQueryClient(<AdminDashboard />);

    await waitFor(() => {
      // Check that timestamps are formatted as time strings
      const timeElements = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/);
      expect(timeElements.length).toBeGreaterThan(0);
    });
  });
});
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import TripMonitoring from '../TripMonitoring';
import { adminService } from '../../../services/admin';

// Mock the admin service
vi.mock('../../../services/admin', () => ({
  adminService: {
    getTrips: vi.fn(),
    updateTripStatus: vi.fn(),
  },
}));

// Mock window.confirm
global.confirm = vi.fn();

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

const mockTripsData = {
  trips: [
    {
      id: '1',
      route: 'Lagos - Abuja',
      origin: 'Lagos',
      destination: 'Abuja',
      bus_number: 'BUS-001',
      bus_model: 'Mercedes Sprinter',
      driver_name: 'John Driver',
      status: 'in_progress',
      departure_time: '2024-01-15T08:00:00Z',
      estimated_arrival: '2024-01-15T14:00:00Z',
      booked_seats: 35,
      capacity: 40,
      fare: 5000,
      total_revenue: 175000,
      payments_completed: 33,
      current_location: {
        lat: 6.5244,
        lng: 3.3792,
        timestamp: '2024-01-15T10:30:00Z',
        speed: 80,
      },
    },
    {
      id: '2',
      route: 'Abuja - Kano',
      origin: 'Abuja',
      destination: 'Kano',
      bus_number: 'BUS-002',
      bus_model: 'Toyota Hiace',
      driver_name: 'Jane Driver',
      status: 'scheduled',
      departure_time: '2024-01-15T10:00:00Z',
      estimated_arrival: '2024-01-15T16:00:00Z',
      booked_seats: 20,
      capacity: 25,
      fare: 4000,
      total_revenue: 80000,
      payments_completed: 18,
      current_location: null,
    },
  ],
  stats: {
    active: 1,
    scheduled: 1,
    completed: 5,
  },
};

describe('TripMonitoring', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders trip monitoring interface', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByText('Trip Monitoring')).toBeInTheDocument();
    });

    // Check header stats
    expect(screen.getByText('1')).toBeInTheDocument(); // Active trips
    expect(screen.getByText('Active Trips')).toBeInTheDocument();
    expect(screen.getByText('Scheduled')).toBeInTheDocument();
    expect(screen.getByText('Completed Today')).toBeInTheDocument();
  });

  it('displays filter controls', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByText('Status:')).toBeInTheDocument();
    });

    // Check filter dropdowns
    expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Today')).toBeInTheDocument();

    // Check refresh button
    expect(screen.getByText('🔄 Refresh')).toBeInTheDocument();
  });

  it('displays trips in card format', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByText('Lagos - Abuja')).toBeInTheDocument();
    });

    // Check trip details
    expect(screen.getByText('Lagos → Abuja')).toBeInTheDocument();
    expect(screen.getByText('BUS-001')).toBeInTheDocument();
    expect(screen.getByText('John Driver')).toBeInTheDocument();
    expect(screen.getByText('35/40')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('in_progress')).toBeInTheDocument();
    expect(screen.getByText('scheduled')).toBeInTheDocument();

    // Check progress bars
    expect(screen.getByText('88% full')).toBeInTheDocument(); // 35/40 = 87.5% rounded
    expect(screen.getByText('80% full')).toBeInTheDocument(); // 20/25 = 80%
  });

  it('handles status filter changes', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
    });

    const statusFilter = screen.getByDisplayValue('All Status');
    fireEvent.change(statusFilter, { target: { value: 'in_progress' } });

    expect(statusFilter.value).toBe('in_progress');
  });

  it('handles date filter changes', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Today')).toBeInTheDocument();
    });

    const dateFilter = screen.getByDisplayValue('Today');
    fireEvent.change(dateFilter, { target: { value: 'week' } });

    expect(dateFilter.value).toBe('week');
  });

  it('opens trip details modal when View Details is clicked', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Trip Details - Lagos - Abuja')).toBeInTheDocument();
    });

    // Check modal content
    expect(screen.getByText('Trip Information')).toBeInTheDocument();
    expect(screen.getByText('Passenger Information')).toBeInTheDocument();
    expect(screen.getByText('Current Location')).toBeInTheDocument();
    expect(screen.getByText('Revenue Information')).toBeInTheDocument();

    // Check specific details (use getAllByText since driver name appears in multiple places)
    expect(screen.getByText('BUS-001 (Mercedes Sprinter)')).toBeInTheDocument();
    expect(screen.getAllByText('John Driver')).toHaveLength(2);
    expect(screen.getByText('35')).toBeInTheDocument(); // Booked seats
    expect(screen.getByText('5')).toBeInTheDocument(); // Available seats
    expect(screen.getByText('88%')).toBeInTheDocument(); // Occupancy
  });

  it('displays location information in modal', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal for trip with location
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Current Location')).toBeInTheDocument();
    });

    // Check location details
    expect(screen.getByText('6.5244, 3.3792')).toBeInTheDocument();
    expect(screen.getByText('80 km/h')).toBeInTheDocument();
  });

  it('handles trip without location data', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal for trip without location
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[1]);

    await waitFor(() => {
      expect(screen.getByText('Current Location')).toBeInTheDocument();
    });

    expect(screen.getByText('Location not available')).toBeInTheDocument();
  });

  it('handles trip status updates', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);
    adminService.updateTripStatus.mockResolvedValue({ success: true });
    global.confirm.mockReturnValue(true);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('Start Trip')).toHaveLength(1);
    });

    // Click start trip button for scheduled trip
    const startTripButton = screen.getByText('Start Trip');
    fireEvent.click(startTripButton);

    expect(global.confirm).toHaveBeenCalledWith(
      'Are you sure you want to change trip status to in_progress?'
    );

    await waitFor(() => {
      expect(adminService.updateTripStatus).toHaveBeenCalledWith('2', 'in_progress');
    });
  });

  it('handles trip status updates from modal', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);
    adminService.updateTripStatus.mockResolvedValue({ success: true });
    global.confirm.mockReturnValue(true);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Trip Actions')).toBeInTheDocument();
    });

    // Click complete trip button
    const completeButton = screen.getByText('Complete Trip');
    fireEvent.click(completeButton);

    expect(global.confirm).toHaveBeenCalledWith(
      'Are you sure you want to change trip status to completed?'
    );

    await waitFor(() => {
      expect(adminService.updateTripStatus).toHaveBeenCalledWith('1', 'completed');
    });
  });

  it('does not update status if user cancels confirmation', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);
    global.confirm.mockReturnValue(false);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('Start Trip')).toHaveLength(1);
    });

    const startTripButton = screen.getByText('Start Trip');
    fireEvent.click(startTripButton);

    expect(global.confirm).toHaveBeenCalled();
    expect(adminService.updateTripStatus).not.toHaveBeenCalled();
  });

  it('closes modal when close button is clicked', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('×')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText('Trip Details - Lagos - Abuja')).not.toBeInTheDocument();
    });
  });

  it('renders loading state', () => {
    adminService.getTrips.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithQueryClient(<TripMonitoring />);

    expect(screen.getByText('Loading trips...')).toBeInTheDocument();
  });

  it('renders error state', async () => {
    const errorMessage = 'Failed to fetch trips';
    adminService.getTrips.mockRejectedValue(new Error(errorMessage));

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByText(`Error loading trips: ${errorMessage}`)).toBeInTheDocument();
    });
  });

  it('handles empty trips data', async () => {
    const emptyData = { trips: [], stats: { active: 0, scheduled: 0, completed: 0 } };
    adminService.getTrips.mockResolvedValue(emptyData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getByText('No trips found')).toBeInTheDocument();
    });
  });

  it('displays correct action buttons based on trip status', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Check that Start Trip button only appears for scheduled trips
    expect(screen.getAllByText('Start Trip')).toHaveLength(1);

    // Check that Track Live button appears for all trips
    expect(screen.getAllByText('Track Live')).toHaveLength(2);
  });

  it('formats departure times correctly', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      // Check that times are formatted correctly (will depend on timezone)
      const timeElements = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/);
      expect(timeElements.length).toBeGreaterThan(0);
    });
  });

  it('calculates occupancy percentage correctly', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      // 35/40 = 87.5% rounded to 88%
      expect(screen.getByText('88% full')).toBeInTheDocument();
      // 20/25 = 80%
      expect(screen.getByText('80% full')).toBeInTheDocument();
    });
  });

  it('displays revenue information in modal', async () => {
    adminService.getTrips.mockResolvedValue(mockTripsData);

    renderWithQueryClient(<TripMonitoring />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Revenue Information')).toBeInTheDocument();
    });

    // Check revenue details
    expect(screen.getByText('$5000')).toBeInTheDocument(); // Fare per seat
    expect(screen.getByText('$175000')).toBeInTheDocument(); // Total revenue
    expect(screen.getByText('33/35 completed')).toBeInTheDocument(); // Payment status
  });
});
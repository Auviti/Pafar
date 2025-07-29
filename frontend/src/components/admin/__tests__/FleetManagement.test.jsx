import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import FleetManagement from '../FleetManagement';
import { adminService } from '../../../services/admin';

// Mock the admin service
vi.mock('../../../services/admin', () => ({
  adminService: {
    getBuses: vi.fn(),
    getDrivers: vi.fn(),
    createBus: vi.fn(),
    updateBus: vi.fn(),
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

const mockBusesData = {
  buses: [
    {
      id: '1',
      license_plate: 'BUS-001',
      model: 'Mercedes Sprinter',
      capacity: 40,
      amenities: ['WiFi', 'AC', 'USB Charging'],
      is_active: true,
      current_trip: 'Lagos - Abuja',
    },
    {
      id: '2',
      license_plate: 'BUS-002',
      model: 'Toyota Hiace',
      capacity: 25,
      amenities: ['AC'],
      is_active: false,
      current_trip: null,
    },
  ],
  total: 2,
};

const mockDriversData = {
  drivers: [
    {
      id: '1',
      first_name: 'John',
      last_name: 'Driver',
      email: 'john.driver@example.com',
      phone: '+1234567890',
      license_number: 'DL123456',
      years_experience: 5,
      status: 'active',
      current_bus: 'BUS-001',
      total_trips: 150,
      avg_rating: 4.8,
    },
    {
      id: '2',
      first_name: 'Jane',
      last_name: 'Driver',
      email: 'jane.driver@example.com',
      phone: '+0987654321',
      license_number: 'DL789012',
      years_experience: 3,
      status: 'inactive',
      current_bus: null,
      total_trips: 75,
      avg_rating: 4.5,
    },
  ],
  total: 2,
};

describe('FleetManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders fleet management interface with buses tab active by default', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.getDrivers.mockResolvedValue(mockDriversData);

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getByText('Fleet Management')).toBeInTheDocument();
    });

    // Check tabs
    expect(screen.getByText('Buses (2)')).toBeInTheDocument();
    expect(screen.getByText('Drivers (2)')).toBeInTheDocument();

    // Check that buses tab is active
    const busesTab = screen.getByText('Buses (2)');
    expect(busesTab).toHaveClass('active');

    // Check add new bus button
    expect(screen.getByText('Add New Bus')).toBeInTheDocument();
  });

  it('displays buses in card format', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getByText('BUS-001')).toBeInTheDocument();
    });

    // Check bus details
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.getByText('40 seats')).toBeInTheDocument();
    expect(screen.getByText('Lagos - Abuja')).toBeInTheDocument();

    // Check amenities
    expect(screen.getByText('WiFi')).toBeInTheDocument();
    expect(screen.getByText('AC')).toBeInTheDocument();
    expect(screen.getByText('USB Charging')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('switches to drivers tab when clicked', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.getDrivers.mockResolvedValue(mockDriversData);

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getByText('Drivers (2)')).toBeInTheDocument();
    });

    const driversTab = screen.getByText('Drivers (2)');
    fireEvent.click(driversTab);

    await waitFor(() => {
      expect(driversTab).toHaveClass('active');
    });

    // Check that Add New Bus button is not visible in drivers tab
    expect(screen.queryByText('Add New Bus')).not.toBeInTheDocument();
  });

  it('displays drivers in card format when drivers tab is active', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.getDrivers.mockResolvedValue(mockDriversData);

    renderWithQueryClient(<FleetManagement />);

    // Switch to drivers tab
    const driversTab = screen.getByText('Drivers (2)');
    fireEvent.click(driversTab);

    await waitFor(() => {
      expect(screen.getByText('John Driver')).toBeInTheDocument();
    });

    // Check driver details
    expect(screen.getByText('john.driver@example.com')).toBeInTheDocument();
    expect(screen.getByText('+1234567890')).toBeInTheDocument();
    expect(screen.getByText('DL123456')).toBeInTheDocument();
    expect(screen.getByText('5 years')).toBeInTheDocument();
    expect(screen.getByText('BUS-001')).toBeInTheDocument();

    // Check driver stats
    expect(screen.getByText('150')).toBeInTheDocument(); // Total trips
    expect(screen.getByText('4.8')).toBeInTheDocument(); // Rating
  });

  it('opens bus modal when Add New Bus is clicked', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getByText('Add New Bus')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add New Bus');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Add New Bus')).toBeInTheDocument();
    });

    // Check modal form fields
    expect(screen.getByLabelText('License Plate *')).toBeInTheDocument();
    expect(screen.getByLabelText('Model *')).toBeInTheDocument();
    expect(screen.getByLabelText('Capacity *')).toBeInTheDocument();
    expect(screen.getByLabelText('Amenities')).toBeInTheDocument();

    // Check amenity checkboxes
    expect(screen.getByText('WiFi')).toBeInTheDocument();
    expect(screen.getByText('AC')).toBeInTheDocument();
    expect(screen.getByText('USB Charging')).toBeInTheDocument();
    expect(screen.getByText('Entertainment')).toBeInTheDocument();
    expect(screen.getByText('Reclining Seats')).toBeInTheDocument();
    expect(screen.getByText('Restroom')).toBeInTheDocument();
  });

  it('opens edit bus modal when Edit button is clicked', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('Edit')).toHaveLength(2);
    });

    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Edit Bus')).toBeInTheDocument();
    });

    // Check that form is pre-filled with bus data
    expect(screen.getByDisplayValue('BUS-001')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.getByDisplayValue('40')).toBeInTheDocument();
  });

  it('handles bus form submission for new bus', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.createBus.mockResolvedValue({ success: true });

    renderWithQueryClient(<FleetManagement />);

    // Open add bus modal
    const addButton = screen.getByText('Add New Bus');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByLabelText('License Plate *')).toBeInTheDocument();
    });

    // Fill form
    fireEvent.change(screen.getByLabelText('License Plate *'), {
      target: { value: 'BUS-003' },
    });
    fireEvent.change(screen.getByLabelText('Model *'), {
      target: { value: 'Ford Transit' },
    });
    fireEvent.change(screen.getByLabelText('Capacity *'), {
      target: { value: '30' },
    });

    // Select amenities
    const wifiCheckbox = screen.getByRole('checkbox', { name: 'WiFi' });
    fireEvent.click(wifiCheckbox);

    // Submit form
    const createButton = screen.getByText('Create Bus');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(adminService.createBus).toHaveBeenCalledWith({
        license_plate: 'BUS-003',
        model: 'Ford Transit',
        capacity: 30,
        amenities: ['WiFi'],
      });
    });
  });

  it('handles bus form submission for editing existing bus', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.updateBus.mockResolvedValue({ success: true });

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('Edit')).toHaveLength(2);
    });

    // Open edit modal
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Edit Bus')).toBeInTheDocument();
    });

    // Modify form
    const modelInput = screen.getByDisplayValue('Mercedes Sprinter');
    fireEvent.change(modelInput, { target: { value: 'Mercedes Sprinter Updated' } });

    // Submit form
    const updateButton = screen.getByText('Update Bus');
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(adminService.updateBus).toHaveBeenCalledWith('1', {
        license_plate: 'BUS-001',
        model: 'Mercedes Sprinter Updated',
        capacity: 40,
        amenities: ['WiFi', 'AC', 'USB Charging'],
      });
    });
  });

  it('closes modal when cancel button is clicked', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    // Open modal
    const addButton = screen.getByText('Add New Bus');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    // Close modal
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByText('Add New Bus')).not.toBeInTheDocument();
    });
  });

  it('closes modal when close (×) button is clicked', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    // Open modal
    const addButton = screen.getByText('Add New Bus');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('×')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByLabelText('License Plate *')).not.toBeInTheDocument();
    });
  });

  it('handles loading state for buses', () => {
    adminService.getBuses.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithQueryClient(<FleetManagement />);

    expect(screen.getByText('Loading buses...')).toBeInTheDocument();
  });

  it('handles loading state for drivers', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.getDrivers.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithQueryClient(<FleetManagement />);

    // Switch to drivers tab
    const driversTab = screen.getByText('Drivers (2)');
    fireEvent.click(driversTab);

    await waitFor(() => {
      expect(screen.getByText('Loading drivers...')).toBeInTheDocument();
    });
  });

  it('handles empty buses data', async () => {
    adminService.getBuses.mockResolvedValue({ buses: [], total: 0 });

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getByText('No buses found')).toBeInTheDocument();
    });
  });

  it('handles empty drivers data', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.getDrivers.mockResolvedValue({ drivers: [], total: 0 });

    renderWithQueryClient(<FleetManagement />);

    // Switch to drivers tab
    const driversTab = screen.getByText('Drivers (0)');
    fireEvent.click(driversTab);

    await waitFor(() => {
      expect(screen.getByText('No drivers found')).toBeInTheDocument();
    });
  });

  it('handles form validation for required fields', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    // Open add bus modal
    const addButton = screen.getByText('Add New Bus');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Create Bus')).toBeInTheDocument();
    });

    // Try to submit without filling required fields
    const createButton = screen.getByText('Create Bus');
    fireEvent.click(createButton);

    // Form should not submit (browser validation will handle this)
    expect(adminService.createBus).not.toHaveBeenCalled();
  });

  it('displays bus action buttons correctly', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);

    renderWithQueryClient(<FleetManagement />);

    await waitFor(() => {
      expect(screen.getAllByText('Edit')).toHaveLength(2);
    });

    // Check that all action buttons are present
    expect(screen.getAllByText('Edit')).toHaveLength(2);
    expect(screen.getByText('Deactivate')).toBeInTheDocument(); // For active bus
    expect(screen.getByText('Activate')).toBeInTheDocument(); // For inactive bus
    expect(screen.getAllByText('View Trips')).toHaveLength(2);
  });

  it('displays driver action buttons correctly', async () => {
    adminService.getBuses.mockResolvedValue(mockBusesData);
    adminService.getDrivers.mockResolvedValue(mockDriversData);

    renderWithQueryClient(<FleetManagement />);

    // Switch to drivers tab
    const driversTab = screen.getByText('Drivers (2)');
    fireEvent.click(driversTab);

    await waitFor(() => {
      expect(screen.getAllByText('View Profile')).toHaveLength(2);
    });

    // Check that all action buttons are present
    expect(screen.getAllByText('View Profile')).toHaveLength(2);
    expect(screen.getAllByText('Assign Bus')).toHaveLength(2);
    expect(screen.getAllByText('View Schedule')).toHaveLength(2);
  });
});
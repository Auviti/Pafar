import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TripSearchForm from '../TripSearchForm';

// Mock the booking service
const mockSearchTrips = vi.fn();
vi.mock('../../../services/booking', () => ({
  searchTrips: mockSearchTrips,
}));

// Mock terminals data
const mockTerminals = [
  { id: '1', name: 'Terminal A', city: 'City A' },
  { id: '2', name: 'Terminal B', city: 'City B' },
  { id: '3', name: 'Terminal C', city: 'City C' },
];

const mockOnSearch = vi.fn();

const renderTripSearchForm = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <TripSearchForm terminals={mockTerminals} onSearch={mockOnSearch} />
    </QueryClientProvider>
  );
};

describe('TripSearchForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search form with all required fields', () => {
    renderTripSearchForm();

    expect(screen.getByText('Search Trips')).toBeInTheDocument();
    expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/to/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/departure date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search trips/i })).toBeInTheDocument();
  });

  it('populates terminal options', () => {
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);

    fireEvent.click(fromSelect);
    expect(screen.getByText('Terminal A - City A')).toBeInTheDocument();
    expect(screen.getByText('Terminal B - City B')).toBeInTheDocument();
    expect(screen.getByText('Terminal C - City C')).toBeInTheDocument();

    fireEvent.click(toSelect);
    expect(screen.getAllByText('Terminal A - City A')).toHaveLength(2);
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    renderTripSearchForm();

    const searchButton = screen.getByRole('button', { name: /search trips/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/origin terminal is required/i)).toBeInTheDocument();
      expect(screen.getByText(/destination terminal is required/i)).toBeInTheDocument();
      expect(screen.getByText(/departure date is required/i)).toBeInTheDocument();
    });
  });

  it('validates that origin and destination are different', async () => {
    const user = userEvent.setup();
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(toSelect, '1');

    const searchButton = screen.getByRole('button', { name: /search trips/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/origin and destination must be different/i)).toBeInTheDocument();
    });
  });

  it('validates departure date is not in the past', async () => {
    const user = userEvent.setup();
    renderTripSearchForm();

    const dateInput = screen.getByLabelText(/departure date/i);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    await user.type(dateInput, yesterday.toISOString().split('T')[0]);

    const searchButton = screen.getByRole('button', { name: /search trips/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/departure date cannot be in the past/i)).toBeInTheDocument();
    });
  });

  it('validates passenger count range', async () => {
    const user = userEvent.setup();
    renderTripSearchForm();

    const passengersInput = screen.getByLabelText(/passengers/i);
    
    // Test minimum
    await user.clear(passengersInput);
    await user.type(passengersInput, '0');

    const searchButton = screen.getByRole('button', { name: /search trips/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/at least 1 passenger required/i)).toBeInTheDocument();
    });

    // Test maximum
    await user.clear(passengersInput);
    await user.type(passengersInput, '11');
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/maximum 10 passengers allowed/i)).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockSearchTrips.mockResolvedValue([]);
    
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);
    const dateInput = screen.getByLabelText(/departure date/i);
    const passengersInput = screen.getByLabelText(/passengers/i);
    const searchButton = screen.getByRole('button', { name: /search trips/i });

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowString = tomorrow.toISOString().split('T')[0];

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(toSelect, '2');
    await user.type(dateInput, tomorrowString);
    await user.clear(passengersInput);
    await user.type(passengersInput, '2');
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith({
        originTerminalId: '1',
        destinationTerminalId: '2',
        departureDate: tomorrowString,
        passengers: 2,
      });
    });
  });

  it('shows loading state during search', async () => {
    const user = userEvent.setup();
    mockSearchTrips.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
    
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);
    const dateInput = screen.getByLabelText(/departure date/i);
    const searchButton = screen.getByRole('button', { name: /search trips/i });

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(toSelect, '2');
    await user.type(dateInput, tomorrow.toISOString().split('T')[0]);
    await user.click(searchButton);

    expect(screen.getByRole('button', { name: /searching/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /searching/i })).toBeDisabled();
  });

  it('swaps origin and destination when swap button is clicked', async () => {
    const user = userEvent.setup();
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);
    const swapButton = screen.getByRole('button', { name: /swap/i });

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(toSelect, '2');
    await user.click(swapButton);

    expect(fromSelect.value).toBe('2');
    expect(toSelect.value).toBe('1');
  });

  it('sets default departure date to today', () => {
    renderTripSearchForm();

    const dateInput = screen.getByLabelText(/departure date/i);
    const today = new Date().toISOString().split('T')[0];
    
    expect(dateInput.value).toBe(today);
  });

  it('sets default passenger count to 1', () => {
    renderTripSearchForm();

    const passengersInput = screen.getByLabelText(/passengers/i);
    expect(passengersInput.value).toBe('1');
  });

  it('displays search results count', async () => {
    const user = userEvent.setup();
    const mockResults = [
      { id: '1', departure_time: '2024-01-01T10:00:00Z' },
      { id: '2', departure_time: '2024-01-01T14:00:00Z' },
    ];
    mockSearchTrips.mockResolvedValue(mockResults);
    
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);
    const dateInput = screen.getByLabelText(/departure date/i);
    const searchButton = screen.getByRole('button', { name: /search trips/i });

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(toSelect, '2');
    await user.type(dateInput, tomorrow.toISOString().split('T')[0]);
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith(expect.objectContaining({
        originTerminalId: '1',
        destinationTerminalId: '2',
      }));
    });
  });

  it('handles search error gracefully', async () => {
    const user = userEvent.setup();
    mockSearchTrips.mockRejectedValue(new Error('Search failed'));
    
    renderTripSearchForm();

    const fromSelect = screen.getByLabelText(/from/i);
    const toSelect = screen.getByLabelText(/to/i);
    const dateInput = screen.getByLabelText(/departure date/i);
    const searchButton = screen.getByRole('button', { name: /search trips/i });

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    await user.selectOptions(fromSelect, '1');
    await user.selectOptions(toSelect, '2');
    await user.type(dateInput, tomorrow.toISOString().split('T')[0]);
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/search failed/i)).toBeInTheDocument();
    });
  });
});
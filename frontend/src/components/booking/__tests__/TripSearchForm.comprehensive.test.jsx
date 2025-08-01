/**
 * Comprehensive tests for TripSearchForm component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TripSearchForm from '../TripSearchForm';

// Mock the booking service
vi.mock('../../../services/booking', () => ({
  searchTrips: vi.fn(),
  getTerminals: vi.fn(),
}));

// Test wrapper component
const TestWrapper = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

const mockTerminals = [
  { id: '1', name: 'New York Central', city: 'New York' },
  { id: '2', name: 'Los Angeles Union', city: 'Los Angeles' },
  { id: '3', name: 'Chicago Central', city: 'Chicago' },
];

const mockTrips = [
  {
    id: '1',
    departure_time: '2024-12-01T10:00:00Z',
    arrival_time: '2024-12-01T18:00:00Z',
    fare: '150.00',
    available_seats: 25,
    bus: { model: 'Luxury Coach', amenities: { wifi: true, ac: true } },
    route: {
      origin_terminal: mockTerminals[0],
      destination_terminal: mockTerminals[1],
    },
  },
  {
    id: '2',
    departure_time: '2024-12-01T14:00:00Z',
    arrival_time: '2024-12-01T22:00:00Z',
    fare: '120.00',
    available_seats: 10,
    bus: { model: 'Standard Coach', amenities: { wifi: false, ac: true } },
    route: {
      origin_terminal: mockTerminals[0],
      destination_terminal: mockTerminals[1],
    },
  },
];

describe('TripSearchForm', () => {
  let user;
  const mockOnSearch = vi.fn();

  beforeEach(() => {
    user = userEvent.setup();
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all form elements', async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/to/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/departure date/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /search trips/i })).toBeInTheDocument();
      });
    });

    it('loads terminals on mount', async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getTerminals).toHaveBeenCalled();
      });
    });

    it('displays loading state while fetching terminals', () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      expect(screen.getByText(/loading terminals/i)).toBeInTheDocument();
    });

    it('handles terminal loading error', async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockRejectedValue(new Error('Failed to load terminals'));

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/failed to load terminals/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    beforeEach(async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);
    });

    it('shows validation errors for empty required fields', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const searchButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/origin is required/i)).toBeInTheDocument();
        expect(screen.getByText(/destination is required/i)).toBeInTheDocument();
        expect(screen.getByText(/departure date is required/i)).toBeInTheDocument();
      });
    });

    it('validates that origin and destination are different', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '1');

      const searchButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/origin and destination must be different/i)).toBeInTheDocument();
      });
    });

    it('validates departure date is not in the past', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/departure date/i)).toBeInTheDocument();
      });

      const dateInput = screen.getByLabelText(/departure date/i);
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayString = yesterday.toISOString().split('T')[0];

      await user.type(dateInput, yesterdayString);

      const searchButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/departure date cannot be in the past/i)).toBeInTheDocument();
      });
    });

    it('validates passenger count is within limits', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
      });

      const passengersInput = screen.getByLabelText(/passengers/i);

      // Test minimum validation
      await user.clear(passengersInput);
      await user.type(passengersInput, '0');

      const searchButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/at least 1 passenger required/i)).toBeInTheDocument();
      });

      // Test maximum validation
      await user.clear(passengersInput);
      await user.type(passengersInput, '11');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/maximum 10 passengers allowed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    beforeEach(async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);
    });

    it('submits form with valid data', async () => {
      const { searchTrips } = await import('../../../services/booking');
      searchTrips.mockResolvedValue(mockTrips);

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const dateInput = screen.getByLabelText(/departure date/i);
      const passengersInput = screen.getByLabelText(/passengers/i);
      const searchButton = screen.getByRole('button', { name: /search trips/i });

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '2');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const tomorrowString = tomorrow.toISOString().split('T')[0];
      await user.type(dateInput, tomorrowString);
      
      await user.clear(passengersInput);
      await user.type(passengersInput, '2');

      await user.click(searchButton);

      await waitFor(() => {
        expect(searchTrips).toHaveBeenCalledWith({
          origin_terminal_id: '1',
          destination_terminal_id: '2',
          departure_date: tomorrowString,
          passengers: 2,
        });
        expect(mockOnSearch).toHaveBeenCalledWith(mockTrips);
      });
    });

    it('shows loading state during search', async () => {
      const { searchTrips } = await import('../../../services/booking');
      searchTrips.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const dateInput = screen.getByLabelText(/departure date/i);
      const searchButton = screen.getByRole('button', { name: /search trips/i });

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '2');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const tomorrowString = tomorrow.toISOString().split('T')[0];
      await user.type(dateInput, tomorrowString);

      await user.click(searchButton);

      expect(screen.getByText(/searching/i)).toBeInTheDocument();
      expect(searchButton).toBeDisabled();
    });

    it('handles search error gracefully', async () => {
      const { searchTrips } = await import('../../../services/booking');
      searchTrips.mockRejectedValue(new Error('No trips found'));

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const dateInput = screen.getByLabelText(/departure date/i);
      const searchButton = screen.getByRole('button', { name: /search trips/i });

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '2');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const tomorrowString = tomorrow.toISOString().split('T')[0];
      await user.type(dateInput, tomorrowString);

      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/no trips found/i)).toBeInTheDocument();
      });

      expect(searchButton).not.toBeDisabled();
    });
  });

  describe('User Interactions', () => {
    beforeEach(async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);
    });

    it('swaps origin and destination when swap button is clicked', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const swapButton = screen.getByRole('button', { name: /swap origin and destination/i });

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '2');

      expect(originSelect).toHaveValue('1');
      expect(destinationSelect).toHaveValue('2');

      await user.click(swapButton);

      expect(originSelect).toHaveValue('2');
      expect(destinationSelect).toHaveValue('1');
    });

    it('updates passenger count with increment/decrement buttons', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
      });

      const passengersInput = screen.getByLabelText(/passengers/i);
      const incrementButton = screen.getByRole('button', { name: /increase passengers/i });
      const decrementButton = screen.getByRole('button', { name: /decrease passengers/i });

      expect(passengersInput).toHaveValue('1');

      await user.click(incrementButton);
      expect(passengersInput).toHaveValue('2');

      await user.click(incrementButton);
      expect(passengersInput).toHaveValue('3');

      await user.click(decrementButton);
      expect(passengersInput).toHaveValue('2');
    });

    it('prevents passenger count from going below 1', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
      });

      const passengersInput = screen.getByLabelText(/passengers/i);
      const decrementButton = screen.getByRole('button', { name: /decrease passengers/i });

      expect(passengersInput).toHaveValue('1');

      await user.click(decrementButton);
      expect(passengersInput).toHaveValue('1');
      expect(decrementButton).toBeDisabled();
    });

    it('prevents passenger count from going above 10', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
      });

      const passengersInput = screen.getByLabelText(/passengers/i);
      const incrementButton = screen.getByRole('button', { name: /increase passengers/i });

      // Set to 10
      await user.clear(passengersInput);
      await user.type(passengersInput, '10');

      await user.click(incrementButton);
      expect(passengersInput).toHaveValue('10');
      expect(incrementButton).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    beforeEach(async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);
    });

    it('has proper ARIA labels and descriptions', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const form = screen.getByRole('form');
      expect(form).toHaveAttribute('aria-label', 'Trip search form');

      const originSelect = screen.getByLabelText(/from/i);
      expect(originSelect).toHaveAttribute('aria-describedby');

      const destinationSelect = screen.getByLabelText(/to/i);
      expect(destinationSelect).toHaveAttribute('aria-describedby');
    });

    it('announces form errors to screen readers', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const searchButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(searchButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/origin is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
        expect(errorMessage).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('has proper keyboard navigation', async () => {
      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const dateInput = screen.getByLabelText(/departure date/i);
      const passengersInput = screen.getByLabelText(/passengers/i);
      const searchButton = screen.getByRole('button', { name: /search trips/i });

      // Tab through form elements
      await user.tab();
      expect(originSelect).toHaveFocus();

      await user.tab();
      expect(destinationSelect).toHaveFocus();

      await user.tab();
      expect(dateInput).toHaveFocus();

      await user.tab();
      expect(passengersInput).toHaveFocus();

      await user.tab();
      expect(searchButton).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    beforeEach(async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue(mockTerminals);
    });

    it('handles empty terminals list', async () => {
      const { getTerminals } = await import('../../../services/booking');
      getTerminals.mockResolvedValue([]);

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/no terminals available/i)).toBeInTheDocument();
      });
    });

    it('handles network timeout', async () => {
      const { searchTrips } = await import('../../../services/booking');
      searchTrips.mockRejectedValue(new Error('Request timeout'));

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const dateInput = screen.getByLabelText(/departure date/i);
      const searchButton = screen.getByRole('button', { name: /search trips/i });

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '2');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const tomorrowString = tomorrow.toISOString().split('T')[0];
      await user.type(dateInput, tomorrowString);

      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/request timeout/i)).toBeInTheDocument();
      });
    });

    it('preserves form state on error', async () => {
      const { searchTrips } = await import('../../../services/booking');
      searchTrips.mockRejectedValue(new Error('Search failed'));

      render(
        <TestWrapper>
          <TripSearchForm onSearch={mockOnSearch} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });

      const originSelect = screen.getByLabelText(/from/i);
      const destinationSelect = screen.getByLabelText(/to/i);
      const dateInput = screen.getByLabelText(/departure date/i);
      const passengersInput = screen.getByLabelText(/passengers/i);
      const searchButton = screen.getByRole('button', { name: /search trips/i });

      await user.selectOptions(originSelect, '1');
      await user.selectOptions(destinationSelect, '2');
      
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const tomorrowString = tomorrow.toISOString().split('T')[0];
      await user.type(dateInput, tomorrowString);
      
      await user.clear(passengersInput);
      await user.type(passengersInput, '3');

      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/search failed/i)).toBeInTheDocument();
      });

      // Form state should be preserved
      expect(originSelect).toHaveValue('1');
      expect(destinationSelect).toHaveValue('2');
      expect(dateInput).toHaveValue(tomorrowString);
      expect(passengersInput).toHaveValue('3');
    });
  });
});
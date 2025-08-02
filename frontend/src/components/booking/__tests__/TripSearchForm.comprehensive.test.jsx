/**
 * Comprehensive tests for TripSearchForm component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockAxios, createMockTrip } from '../../test/test-utils';
import TripSearchForm from '../TripSearchForm';

// Mock dependencies
vi.mock('axios', () => ({
  default: mockAxios,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('TripSearchForm', () => {
  let mockOnSearch;
  let mockOnError;
  let user;

  const mockTerminals = [
    { id: '1', name: 'Central Terminal', city: 'New York' },
    { id: '2', name: 'Airport Terminal', city: 'Los Angeles' },
    { id: '3', name: 'Downtown Station', city: 'Chicago' },
  ];

  beforeEach(() => {
    mockOnSearch = vi.fn();
    mockOnError = vi.fn();
    user = userEvent.setup();
    
    // Mock terminals API response
    mockAxios.get.mockResolvedValue({
      data: mockTerminals,
    });
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders all form elements correctly', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/to/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/departure date/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/return date/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /search trips/i })).toBeInTheDocument();
      });
    });

    it('loads terminals on component mount', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        expect(mockAxios.get).toHaveBeenCalledWith('/api/v1/terminals');
      });
    });

    it('renders loading state while fetching terminals', () => {
      // Mock pending request
      mockAxios.get.mockImplementation(() => new Promise(() => {}));

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      expect(screen.getByTestId('terminals-loading')).toBeInTheDocument();
    });

    it('renders error state when terminals fail to load', async () => {
      mockAxios.get.mockRejectedValue(new Error('Failed to load terminals'));

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load terminals/i)).toBeInTheDocument();
      });
    });

    it('renders with default values when provided', () => {
      const defaultValues = {
        originTerminalId: '1',
        destinationTerminalId: '2',
        departureDate: '2024-12-25',
        passengers: 2,
      };

      render(
        <TripSearchForm 
          onSearch={mockOnSearch} 
          onError={mockOnError}
          defaultValues={defaultValues}
        />
      );

      expect(screen.getByDisplayValue('2024-12-25')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2')).toBeInTheDocument();
    });
  });

  describe('Terminal Selection', () => {
    it('populates terminal dropdowns with fetched data', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);

        expect(fromSelect).toBeInTheDocument();
        expect(toSelect).toBeInTheDocument();
      });

      // Check if options are populated
      const fromOptions = screen.getAllByText(/central terminal/i);
      expect(fromOptions.length).toBeGreaterThan(0);
    });

    it('filters out selected origin from destination options', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        fireEvent.change(fromSelect, { target: { value: '1' } });
      });

      // Destination dropdown should not include the selected origin
      const toSelect = screen.getByLabelText(/to/i);
      const toOptions = Array.from(toSelect.options).map(option => option.value);
      expect(toOptions).not.toContain('1');
    });

    it('supports terminal search/autocomplete', async () => {
      render(
        <TripSearchForm 
          onSearch={mockOnSearch} 
          onError={mockOnError}
          enableAutocomplete={true}
        />
      );

      await waitFor(() => {
        const fromInput = screen.getByLabelText(/from/i);
        expect(fromInput).toBeInTheDocument();
      });

      // Type to search
      const fromInput = screen.getByLabelText(/from/i);
      await user.type(fromInput, 'Central');

      await waitFor(() => {
        expect(screen.getByText(/central terminal/i)).toBeInTheDocument();
      });
    });

    it('swaps origin and destination when swap button is clicked', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);

        fireEvent.change(fromSelect, { target: { value: '1' } });
        fireEvent.change(toSelect, { target: { value: '2' } });
      });

      const swapButton = screen.getByRole('button', { name: /swap locations/i });
      await user.click(swapButton);

      const fromSelect = screen.getByLabelText(/from/i);
      const toSelect = screen.getByLabelText(/to/i);

      expect(fromSelect.value).toBe('2');
      expect(toSelect.value).toBe('1');
    });
  });

  describe('Date Selection', () => {
    it('sets minimum date to today', () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const departureDateInput = screen.getByLabelText(/departure date/i);
      const today = new Date().toISOString().split('T')[0];
      
      expect(departureDateInput).toHaveAttribute('min', today);
    });

    it('sets return date minimum to departure date', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const departureDateInput = screen.getByLabelText(/departure date/i);
      const returnDateInput = screen.getByLabelText(/return date/i);

      await user.type(departureDateInput, '2024-12-25');

      await waitFor(() => {
        expect(returnDateInput).toHaveAttribute('min', '2024-12-25');
      });
    });

    it('shows/hides return date based on trip type', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const roundTripRadio = screen.getByLabelText(/round trip/i);
      const oneWayRadio = screen.getByLabelText(/one way/i);
      
      // Initially round trip should be selected
      expect(screen.getByLabelText(/return date/i)).toBeInTheDocument();

      // Switch to one way
      await user.click(oneWayRadio);
      expect(screen.queryByLabelText(/return date/i)).not.toBeInTheDocument();

      // Switch back to round trip
      await user.click(roundTripRadio);
      expect(screen.getByLabelText(/return date/i)).toBeInTheDocument();
    });

    it('validates departure date is not in the past', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const departureDateInput = screen.getByLabelText(/departure date/i);
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayString = yesterday.toISOString().split('T')[0];

      await user.type(departureDateInput, yesterdayString);

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/departure date cannot be in the past/i)).toBeInTheDocument();
      });
    });
  });

  describe('Passenger Selection', () => {
    it('allows passenger count selection', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const passengerSelect = screen.getByLabelText(/passengers/i);
      await user.selectOptions(passengerSelect, '3');

      expect(passengerSelect.value).toBe('3');
    });

    it('limits maximum passenger count', () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const passengerSelect = screen.getByLabelText(/passengers/i);
      const options = Array.from(passengerSelect.options).map(option => parseInt(option.value));
      const maxPassengers = Math.max(...options);

      expect(maxPassengers).toBeLessThanOrEqual(10); // Reasonable limit
    });

    it('shows passenger type breakdown for multiple passengers', async () => {
      render(
        <TripSearchForm 
          onSearch={mockOnSearch} 
          onError={mockOnError}
          showPassengerTypes={true}
        />
      );

      const passengerSelect = screen.getByLabelText(/passengers/i);
      await user.selectOptions(passengerSelect, '3');

      await waitFor(() => {
        expect(screen.getByLabelText(/adults/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/children/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('validates required fields', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select origin terminal/i)).toBeInTheDocument();
        expect(screen.getByText(/please select destination terminal/i)).toBeInTheDocument();
        expect(screen.getByText(/please select departure date/i)).toBeInTheDocument();
      });
    });

    it('validates origin and destination are different', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);

        fireEvent.change(fromSelect, { target: { value: '1' } });
        fireEvent.change(toSelect, { target: { value: '1' } });
      });

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/origin and destination must be different/i)).toBeInTheDocument();
      });
    });

    it('validates return date is after departure date', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const departureDateInput = screen.getByLabelText(/departure date/i);
      const returnDateInput = screen.getByLabelText(/return date/i);

      await user.type(departureDateInput, '2024-12-25');
      await user.type(returnDateInput, '2024-12-24');

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/return date must be after departure date/i)).toBeInTheDocument();
      });
    });

    it('clears validation errors when user corrects input', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      // Trigger validation error
      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select origin terminal/i)).toBeInTheDocument();
      });

      // Correct the input
      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        fireEvent.change(fromSelect, { target: { value: '1' } });
      });

      await waitFor(() => {
        expect(screen.queryByText(/please select origin terminal/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);
        const departureDateInput = screen.getByLabelText(/departure date/i);
        const passengerSelect = screen.getByLabelText(/passengers/i);

        fireEvent.change(fromSelect, { target: { value: '1' } });
        fireEvent.change(toSelect, { target: { value: '2' } });
        fireEvent.change(departureDateInput, { target: { value: '2024-12-25' } });
        fireEvent.change(passengerSelect, { target: { value: '2' } });
      });

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSearch).toHaveBeenCalledWith({
          originTerminalId: '1',
          destinationTerminalId: '2',
          departureDate: '2024-12-25',
          returnDate: null,
          passengers: 2,
          tripType: 'one-way',
        });
      });
    });

    it('submits round trip data correctly', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const roundTripRadio = screen.getByLabelText(/round trip/i);
        fireEvent.click(roundTripRadio);

        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);
        const departureDateInput = screen.getByLabelText(/departure date/i);
        const returnDateInput = screen.getByLabelText(/return date/i);

        fireEvent.change(fromSelect, { target: { value: '1' } });
        fireEvent.change(toSelect, { target: { value: '2' } });
        fireEvent.change(departureDateInput, { target: { value: '2024-12-25' } });
        fireEvent.change(returnDateInput, { target: { value: '2024-12-30' } });
      });

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSearch).toHaveBeenCalledWith({
          originTerminalId: '1',
          destinationTerminalId: '2',
          departureDate: '2024-12-25',
          returnDate: '2024-12-30',
          passengers: 1,
          tripType: 'round-trip',
        });
      });
    });

    it('shows loading state during search', async () => {
      // Mock delayed search
      mockOnSearch.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);
        const departureDateInput = screen.getByLabelText(/departure date/i);

        fireEvent.change(fromSelect, { target: { value: '1' } });
        fireEvent.change(toSelect, { target: { value: '2' } });
        fireEvent.change(departureDateInput, { target: { value: '2024-12-25' } });
      });

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      expect(screen.getByText(/searching/i)).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Recent Searches', () => {
    it('displays recent searches when available', () => {
      const recentSearches = [
        {
          originTerminalId: '1',
          destinationTerminalId: '2',
          departureDate: '2024-12-25',
          passengers: 2,
        },
      ];

      render(
        <TripSearchForm 
          onSearch={mockOnSearch} 
          onError={mockOnError}
          recentSearches={recentSearches}
        />
      );

      expect(screen.getByText(/recent searches/i)).toBeInTheDocument();
    });

    it('allows selecting from recent searches', async () => {
      const recentSearches = [
        {
          originTerminalId: '1',
          destinationTerminalId: '2',
          departureDate: '2024-12-25',
          passengers: 2,
          label: 'New York to Los Angeles',
        },
      ];

      render(
        <TripSearchForm 
          onSearch={mockOnSearch} 
          onError={mockOnError}
          recentSearches={recentSearches}
        />
      );

      const recentSearchButton = screen.getByText(/new york to los angeles/i);
      await user.click(recentSearchButton);

      // Form should be populated with recent search data
      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);
        
        expect(fromSelect.value).toBe('1');
        expect(toSelect.value).toBe('2');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        expect(screen.getByRole('form')).toBeInTheDocument();
        expect(screen.getByLabelText(/from/i)).toHaveAttribute('aria-required', 'true');
        expect(screen.getByLabelText(/to/i)).toHaveAttribute('aria-required', 'true');
        expect(screen.getByLabelText(/departure date/i)).toHaveAttribute('aria-required', 'true');
      });
    });

    it('announces validation errors to screen readers', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        const errorElement = screen.getByText(/please select origin terminal/i);
        expect(errorElement).toHaveAttribute('role', 'alert');
        expect(errorElement).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('supports keyboard navigation', async () => {
      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);
        const departureDateInput = screen.getByLabelText(/departure date/i);

        // Tab through form elements
        fromSelect.focus();
        expect(fromSelect).toHaveFocus();

        fireEvent.keyDown(fromSelect, { key: 'Tab' });
        expect(toSelect).toHaveFocus();

        fireEvent.keyDown(toSelect, { key: 'Tab' });
        expect(departureDateInput).toHaveFocus();
      });
    });
  });

  describe('Mobile Responsiveness', () => {
    it('adapts layout for mobile screens', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const form = screen.getByRole('form');
      expect(form).toHaveClass('mobile-layout');
    });

    it('shows mobile-optimized date picker', () => {
      // Mock mobile device
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        configurable: true,
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
      });

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const departureDateInput = screen.getByLabelText(/departure date/i);
      expect(departureDateInput).toHaveAttribute('type', 'date');
    });
  });

  describe('Performance', () => {
    it('debounces terminal search', async () => {
      const mockSearchTerminals = vi.fn();
      
      render(
        <TripSearchForm 
          onSearch={mockOnSearch} 
          onError={mockOnError}
          onSearchTerminals={mockSearchTerminals}
          enableAutocomplete={true}
        />
      );

      await waitFor(() => {
        const fromInput = screen.getByLabelText(/from/i);
        
        // Type rapidly
        fireEvent.change(fromInput, { target: { value: 'C' } });
        fireEvent.change(fromInput, { target: { value: 'Ce' } });
        fireEvent.change(fromInput, { target: { value: 'Cen' } });
        fireEvent.change(fromInput, { target: { value: 'Cent' } });
      });

      // Search should be debounced
      await waitFor(() => {
        expect(mockSearchTerminals).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    it('memoizes terminal options', () => {
      const { rerender } = render(
        <TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />
      );

      const initialOptions = screen.getAllByRole('option');

      // Re-render with same terminals
      rerender(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      const secondOptions = screen.getAllByRole('option');

      // Options should be memoized
      expect(initialOptions.length).toBe(secondOptions.length);
    });
  });

  describe('Error Handling', () => {
    it('handles terminal loading errors gracefully', async () => {
      mockAxios.get.mockRejectedValue(new Error('Network error'));

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load terminals/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('allows retry after terminal loading error', async () => {
      // First attempt fails
      mockAxios.get.mockRejectedValueOnce(new Error('Network error'));

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load terminals/i)).toBeInTheDocument();
      });

      // Second attempt succeeds
      mockAxios.get.mockResolvedValueOnce({ data: mockTerminals });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.queryByText(/failed to load terminals/i)).not.toBeInTheDocument();
        expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
      });
    });

    it('handles search errors gracefully', async () => {
      mockOnSearch.mockRejectedValue(new Error('Search failed'));

      render(<TripSearchForm onSearch={mockOnSearch} onError={mockOnError} />);

      await waitFor(() => {
        const fromSelect = screen.getByLabelText(/from/i);
        const toSelect = screen.getByLabelText(/to/i);
        const departureDateInput = screen.getByLabelText(/departure date/i);

        fireEvent.change(fromSelect, { target: { value: '1' } });
        fireEvent.change(toSelect, { target: { value: '2' } });
        fireEvent.change(departureDateInput, { target: { value: '2024-12-25' } });
      });

      const submitButton = screen.getByRole('button', { name: /search trips/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Search failed');
      });
    });
  });
});
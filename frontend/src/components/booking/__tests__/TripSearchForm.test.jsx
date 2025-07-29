import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import TripSearchForm from '../TripSearchForm';
import { bookingService } from '../../../services/booking';

// Mock the booking service
vi.mock('../../../services/booking', () => ({
  bookingService: {
    getTerminals: vi.fn()
  }
}));

const mockTerminals = [
  { id: '1', name: 'Central Terminal', city: 'New York' },
  { id: '2', name: 'Airport Terminal', city: 'Los Angeles' },
  { id: '3', name: 'Downtown Station', city: 'Chicago' }
];

describe('TripSearchForm', () => {
  const mockOnSearch = vi.fn();
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    bookingService.getTerminals.mockResolvedValue({ terminals: mockTerminals });
  });

  it('renders search form with all fields', async () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    expect(screen.getByRole('heading', { name: 'Search Trips' })).toBeInTheDocument();
    expect(screen.getByText('Find and book your perfect journey')).toBeInTheDocument();
    
    expect(screen.getByLabelText('From')).toBeInTheDocument();
    expect(screen.getByLabelText('To')).toBeInTheDocument();
    expect(screen.getByLabelText('Departure Date')).toBeInTheDocument();
    expect(screen.getByLabelText('Passengers')).toBeInTheDocument();
    
    expect(screen.getByRole('button', { name: 'Search Trips' })).toBeInTheDocument();
  });

  it('loads terminals on mount', async () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    await waitFor(() => {
      expect(bookingService.getTerminals).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(screen.getAllByText('Central Terminal - New York')).toHaveLength(2);
      expect(screen.getAllByText('Airport Terminal - Los Angeles')).toHaveLength(2);
      expect(screen.getAllByText('Downtown Station - Chicago')).toHaveLength(2);
    });
  });

  it('validates required fields', async () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    const searchButton = screen.getByRole('button', { name: 'Search Trips' });
    await user.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Please select origin terminal')).toBeInTheDocument();
      expect(screen.getByText('Please select destination terminal')).toBeInTheDocument();
    });

    expect(mockOnSearch).not.toHaveBeenCalled();
  });

  it('prevents same origin and destination selection', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    
    render(<TripSearchForm onSearch={mockOnSearch} />);

    await waitFor(() => {
      expect(screen.getAllByText('Central Terminal - New York')).toHaveLength(2);
    });

    const originSelect = screen.getByLabelText('From');
    const destinationSelect = screen.getByLabelText('To');
    const searchButton = screen.getByRole('button', { name: 'Search Trips' });

    await user.selectOptions(originSelect, '1');
    await user.selectOptions(destinationSelect, '1');
    await user.click(searchButton);

    expect(alertSpy).toHaveBeenCalledWith('Origin and destination terminals cannot be the same');
    expect(mockOnSearch).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });

  it('submits form with valid data', async () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    await waitFor(() => {
      expect(screen.getAllByText('Central Terminal - New York')).toHaveLength(2);
    });

    const originSelect = screen.getByLabelText('From');
    const destinationSelect = screen.getByLabelText('To');
    const dateInput = screen.getByLabelText('Departure Date');
    const passengersSelect = screen.getByLabelText('Passengers');
    const searchButton = screen.getByRole('button', { name: 'Search Trips' });

    await user.selectOptions(originSelect, '1');
    await user.selectOptions(destinationSelect, '2');
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);
    const futureDateStr = futureDate.toISOString().split('T')[0];
    fireEvent.change(dateInput, { target: { value: futureDateStr } });
    await user.selectOptions(passengersSelect, '2');
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith({
        originTerminalId: '1',
        destinationTerminalId: '2',
        departureDate: '2024-12-25',
        passengers: 2
      });
    });
  });

  it('swaps terminals when swap button is clicked', async () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    await waitFor(() => {
      expect(screen.getAllByText('Central Terminal - New York')).toHaveLength(2);
    });

    const originSelect = screen.getByLabelText('From');
    const destinationSelect = screen.getByLabelText('To');
    const swapButton = screen.getByTitle('Swap origin and destination');

    await user.selectOptions(originSelect, '1');
    await user.selectOptions(destinationSelect, '2');

    expect(originSelect.value).toBe('1');
    expect(destinationSelect.value).toBe('2');

    await user.click(swapButton);

    expect(originSelect.value).toBe('2');
    expect(destinationSelect.value).toBe('1');
  });

  it('disables swap button when terminals are not selected', async () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    const swapButton = screen.getByTitle('Swap origin and destination');
    expect(swapButton).toBeDisabled();

    await waitFor(() => {
      expect(screen.getAllByText('Central Terminal - New York')).toHaveLength(2);
    });

    const originSelect = screen.getByLabelText('From');
    await user.selectOptions(originSelect, '1');

    expect(swapButton).toBeDisabled();

    const destinationSelect = screen.getByLabelText('To');
    await user.selectOptions(destinationSelect, '2');

    expect(swapButton).not.toBeDisabled();
  });

  it('sets default values correctly', () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    const dateInput = screen.getByLabelText('Departure Date');
    const passengersSelect = screen.getByLabelText('Passengers');

    const today = new Date().toISOString().split('T')[0];
    expect(dateInput.value).toBe(today);
    expect(passengersSelect.value).toBe('1');
  });

  it('shows loading state', () => {
    render(<TripSearchForm onSearch={mockOnSearch} loading={true} />);

    const searchButton = screen.getByRole('button', { name: 'Searching...' });
    expect(searchButton).toBeDisabled();
  });

  it('handles terminal loading error gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    bookingService.getTerminals.mockRejectedValue(new Error('Network error'));

    render(<TripSearchForm onSearch={mockOnSearch} />);

    await waitFor(() => {
      expect(bookingService.getTerminals).toHaveBeenCalledTimes(1);
    });

    // Form should still be rendered even if terminals fail to load
    expect(screen.getByRole('heading', { name: 'Search Trips' })).toBeInTheDocument();
    expect(screen.getByLabelText('From')).toBeInTheDocument();

    consoleErrorSpy.mockRestore();
  });

  it('validates date range', () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    const dateInput = screen.getByLabelText('Departure Date');
    const today = new Date().toISOString().split('T')[0];
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 90);
    const maxDateStr = maxDate.toISOString().split('T')[0];

    expect(dateInput.getAttribute('min')).toBe(today);
    expect(dateInput.getAttribute('max')).toBe(maxDateStr);
  });

  it('validates passenger count options', () => {
    render(<TripSearchForm onSearch={mockOnSearch} />);

    const passengersSelect = screen.getByLabelText('Passengers');
    const options = Array.from(passengersSelect.options).map(option => ({
      value: option.value,
      text: option.text
    }));

    expect(options).toEqual([
      { value: '1', text: '1 Passenger' },
      { value: '2', text: '2 Passengers' },
      { value: '3', text: '3 Passengers' },
      { value: '4', text: '4 Passengers' },
      { value: '5', text: '5 Passengers' },
      { value: '6', text: '6 Passengers' },
      { value: '7', text: '7 Passengers' },
      { value: '8', text: '8 Passengers' },
      { value: '9', text: '9 Passengers' },
      { value: '10', text: '10 Passengers' }
    ]);
  });
});
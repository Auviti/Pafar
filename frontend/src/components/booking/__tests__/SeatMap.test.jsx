import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SeatMap from '../SeatMap';

const mockTrip = {
  id: '1',
  bus: {
    id: '1',
    capacity: 50,
    model: 'Mercedes Sprinter',
  },
  available_seats: 45,
};

const mockOccupiedSeats = [1, 5, 10, 15, 20];
const mockSelectedSeats = [2, 3];
const mockOnSeatSelect = vi.fn();
const mockOnSeatDeselect = vi.fn();

const defaultProps = {
  trip: mockTrip,
  occupiedSeats: mockOccupiedSeats,
  selectedSeats: mockSelectedSeats,
  onSeatSelect: mockOnSeatSelect,
  onSeatDeselect: mockOnSeatDeselect,
  maxSeats: 4,
};

describe('SeatMap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders seat map with correct layout', () => {
    render(<SeatMap {...defaultProps} />);

    expect(screen.getByText('Select Your Seats')).toBeInTheDocument();
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.getByText('45 seats available')).toBeInTheDocument();
    
    // Check seat legend
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByText('Selected')).toBeInTheDocument();
    expect(screen.getByText('Occupied')).toBeInTheDocument();
  });

  it('displays seats in correct grid layout', () => {
    render(<SeatMap {...defaultProps} />);

    // Should have 50 seats (capacity)
    const seats = screen.getAllByRole('button', { name: /seat/i });
    expect(seats).toHaveLength(50);

    // Check first few seat numbers
    expect(screen.getByRole('button', { name: /seat 1/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /seat 2/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /seat 50/i })).toBeInTheDocument();
  });

  it('shows correct seat states', () => {
    render(<SeatMap {...defaultProps} />);

    // Occupied seats should be disabled
    const occupiedSeat = screen.getByRole('button', { name: /seat 1/i });
    expect(occupiedSeat).toBeDisabled();
    expect(occupiedSeat).toHaveClass('seat-occupied');

    // Selected seats should have selected class
    const selectedSeat = screen.getByRole('button', { name: /seat 2/i });
    expect(selectedSeat).toHaveClass('seat-selected');

    // Available seats should be clickable
    const availableSeat = screen.getByRole('button', { name: /seat 4/i });
    expect(availableSeat).not.toBeDisabled();
    expect(availableSeat).toHaveClass('seat-available');
  });

  it('handles seat selection', async () => {
    const user = userEvent.setup();
    render(<SeatMap {...defaultProps} />);

    const availableSeat = screen.getByRole('button', { name: /seat 4/i });
    await user.click(availableSeat);

    expect(mockOnSeatSelect).toHaveBeenCalledWith(4);
  });

  it('handles seat deselection', async () => {
    const user = userEvent.setup();
    render(<SeatMap {...defaultProps} />);

    const selectedSeat = screen.getByRole('button', { name: /seat 2/i });
    await user.click(selectedSeat);

    expect(mockOnSeatDeselect).toHaveBeenCalledWith(2);
  });

  it('prevents selection when max seats reached', async () => {
    const user = userEvent.setup();
    const propsWithMaxSeats = {
      ...defaultProps,
      selectedSeats: [2, 3, 6, 7], // Already at max (4 seats)
    };
    
    render(<SeatMap {...propsWithMaxSeats} />);

    const availableSeat = screen.getByRole('button', { name: /seat 4/i });
    await user.click(availableSeat);

    expect(mockOnSeatSelect).not.toHaveBeenCalled();
    expect(screen.getByText(/maximum 4 seats can be selected/i)).toBeInTheDocument();
  });

  it('shows seat selection counter', () => {
    render(<SeatMap {...defaultProps} />);

    expect(screen.getByText('2 of 4 seats selected')).toBeInTheDocument();
  });

  it('displays seat prices', () => {
    const propsWithPricing = {
      ...defaultProps,
      trip: {
        ...mockTrip,
        fare: 25.00,
      },
    };

    render(<SeatMap {...propsWithPricing} />);

    expect(screen.getByText('$25.00 per seat')).toBeInTheDocument();
    expect(screen.getByText('Total: $50.00')).toBeInTheDocument(); // 2 selected seats
  });

  it('handles different bus layouts', () => {
    const propsWithSmallBus = {
      ...defaultProps,
      trip: {
        ...mockTrip,
        bus: {
          ...mockTrip.bus,
          capacity: 20,
        },
      },
    };

    render(<SeatMap {...propsWithSmallBus} />);

    const seats = screen.getAllByRole('button', { name: /seat/i });
    expect(seats).toHaveLength(20);
  });

  it('shows driver seat as unavailable', () => {
    render(<SeatMap {...defaultProps} />);

    // Assuming seat 1 is driver seat in this layout
    const driverArea = screen.getByText('Driver');
    expect(driverArea).toBeInTheDocument();
  });

  it('displays seat tooltips on hover', async () => {
    const user = userEvent.setup();
    render(<SeatMap {...defaultProps} />);

    const availableSeat = screen.getByRole('button', { name: /seat 4/i });
    await user.hover(availableSeat);

    expect(screen.getByText('Seat 4 - Available')).toBeInTheDocument();
  });

  it('shows occupied seat tooltips', async () => {
    const user = userEvent.setup();
    render(<SeatMap {...defaultProps} />);

    const occupiedSeat = screen.getByRole('button', { name: /seat 1/i });
    await user.hover(occupiedSeat);

    expect(screen.getByText('Seat 1 - Occupied')).toBeInTheDocument();
  });

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    render(<SeatMap {...defaultProps} />);

    const firstAvailableSeat = screen.getByRole('button', { name: /seat 4/i });
    firstAvailableSeat.focus();

    await user.keyboard('{Enter}');
    expect(mockOnSeatSelect).toHaveBeenCalledWith(4);

    await user.keyboard('{Space}');
    expect(mockOnSeatSelect).toHaveBeenCalledTimes(2);
  });

  it('shows seat map in different views', () => {
    const propsWithView = {
      ...defaultProps,
      view: 'compact',
    };

    render(<SeatMap {...propsWithView} />);

    const seatMap = screen.getByTestId('seat-map');
    expect(seatMap).toHaveClass('seat-map-compact');
  });

  it('handles empty occupied seats array', () => {
    const propsWithNoOccupied = {
      ...defaultProps,
      occupiedSeats: [],
    };

    render(<SeatMap {...propsWithNoOccupied} />);

    expect(screen.getByText('50 seats available')).toBeInTheDocument();
  });

  it('handles empty selected seats array', () => {
    const propsWithNoSelected = {
      ...defaultProps,
      selectedSeats: [],
    };

    render(<SeatMap {...propsWithNoSelected} />);

    expect(screen.getByText('0 of 4 seats selected')).toBeInTheDocument();
    expect(screen.getByText('Total: $0.00')).toBeInTheDocument();
  });

  it('shows accessibility information', () => {
    render(<SeatMap {...defaultProps} />);

    expect(screen.getByText(/use arrow keys to navigate/i)).toBeInTheDocument();
    expect(screen.getByText(/press enter or space to select/i)).toBeInTheDocument();
  });

  it('handles seat map loading state', () => {
    const propsWithLoading = {
      ...defaultProps,
      isLoading: true,
    };

    render(<SeatMap {...propsWithLoading} />);

    expect(screen.getByText('Loading seat map...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles seat map error state', () => {
    const propsWithError = {
      ...defaultProps,
      error: 'Failed to load seat map',
    };

    render(<SeatMap {...propsWithError} />);

    expect(screen.getByText('Failed to load seat map')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import SeatMap from '../SeatMap';

const mockTrip = {
  id: '1',
  origin_terminal: { name: 'Central Terminal', city: 'New York' },
  destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
  bus: {
    model: 'Mercedes Sprinter',
    license_plate: 'ABC-123',
    capacity: 20
  },
  occupied_seats: [1, 3, 5, 10, 15]
};

describe('SeatMap', () => {
  const mockOnSeatSelect = vi.fn();
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
        loading={true} 
      />
    );

    expect(screen.getByText('Loading seat map...')).toBeInTheDocument();
  });

  it('shows empty state when no trip is provided', () => {
    render(
      <SeatMap 
        trip={null} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    expect(screen.getByText('Please select a trip to view seat map')).toBeInTheDocument();
  });

  it('displays trip information correctly', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    expect(screen.getByText('Select Your Seats')).toBeInTheDocument();
    expect(screen.getByText('Central Terminal → Airport Terminal')).toBeInTheDocument();
    expect(screen.getByText('Mercedes Sprinter - ABC-123')).toBeInTheDocument();
  });

  it('displays seat legend', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByText('Selected')).toBeInTheDocument();
    expect(screen.getByText('Occupied')).toBeInTheDocument();
  });

  it('generates correct seat layout', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    // Should have seats 1-20 for capacity of 20
    for (let i = 1; i <= 20; i++) {
      expect(screen.getByTitle(new RegExp(`Seat ${i}`))).toBeInTheDocument();
    }

    // Should have 5 rows (20 seats / 4 seats per row)
    const rows = screen.getAllByText(/^\d+$/);
    expect(rows).toHaveLength(5);
  });

  it('shows occupied seats correctly', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    // Check occupied seats
    const occupiedSeats = [1, 3, 5, 10, 15];
    occupiedSeats.forEach(seatNumber => {
      const seat = screen.getByTitle(new RegExp(`Seat ${seatNumber}.*occupied`));
      expect(seat).toBeInTheDocument();
      expect(seat).toBeDisabled();
    });
  });

  it('allows selecting available seats', async () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    const availableSeat = screen.getByTitle('Seat 2A - available');
    await user.click(availableSeat);

    expect(mockOnSeatSelect).toHaveBeenCalledWith([2]);
  });

  it('allows deselecting selected seats', async () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[2]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    const selectedSeat = screen.getByTitle('Seat 2A - selected');
    await user.click(selectedSeat);

    expect(mockOnSeatSelect).toHaveBeenCalledWith([]);
  });

  it('prevents selecting occupied seats', async () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    const occupiedSeat = screen.getByTitle('Seat 1A - occupied');
    expect(occupiedSeat).toBeDisabled();

    await user.click(occupiedSeat);
    expect(mockOnSeatSelect).not.toHaveBeenCalled();
  });

  it('respects maximum seat selection limit', async () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[2]} 
        onSeatSelect={mockOnSeatSelect} 
        maxSeats={2}
      />
    );

    const availableSeat = screen.getByTitle('Seat 4B - available');
    await user.click(availableSeat);

    expect(mockOnSeatSelect).toHaveBeenCalledWith([2, 4]);

    // Try to select a third seat
    const anotherSeat = screen.getByTitle('Seat 6B - available');
    await user.click(anotherSeat);

    // Should replace the first selected seat
    expect(mockOnSeatSelect).toHaveBeenCalledWith([4, 6]);
  });

  it('displays selected seats in summary', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[2, 4, 6]} 
        onSeatSelect={mockOnSeatSelect} 
        maxSeats={5}
      />
    );

    expect(screen.getByText('Selected Seats (3/5):')).toBeInTheDocument();
    expect(screen.getByText('Seat 2')).toBeInTheDocument();
    expect(screen.getByText('Seat 4')).toBeInTheDocument();
    expect(screen.getByText('Seat 6')).toBeInTheDocument();
  });

  it('shows no seats selected message when none selected', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    expect(screen.getByText('Selected Seats (0/1):')).toBeInTheDocument();
    expect(screen.getByText('No seats selected')).toBeInTheDocument();
  });

  it('allows removing seats from selection summary', async () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[2, 4]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    const removeButtons = screen.getAllByText('×');
    await user.click(removeButtons[0]); // Remove first seat

    expect(mockOnSeatSelect).toHaveBeenCalledWith([4]);
  });

  it('shows selection tip for multiple seats', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
        maxSeats={3}
      />
    );

    expect(screen.getByText('💡 You can select up to 3 seats for your booking')).toBeInTheDocument();
  });

  it('does not show selection tip for single seat', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
        maxSeats={1}
      />
    );

    expect(screen.queryByText(/You can select up to/)).not.toBeInTheDocument();
  });

  it('displays bus layout with driver area', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    expect(screen.getByText('🚗 Driver')).toBeInTheDocument();
    expect(screen.getByText('Back')).toBeInTheDocument();
  });

  it('shows correct seat icons based on status', () => {
    render(
      <SeatMap 
        trip={mockTrip} 
        selectedSeats={[2]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    // Available seat should show 💺
    const availableSeat = screen.getByTitle('Seat 4B - available');
    expect(availableSeat).toHaveTextContent('💺');

    // Selected seat should show ✅
    const selectedSeat = screen.getByTitle('Seat 2A - selected');
    expect(selectedSeat).toHaveTextContent('✅');

    // Occupied seat should show 🚫
    const occupiedSeat = screen.getByTitle('Seat 1A - occupied');
    expect(occupiedSeat).toHaveTextContent('🚫');
  });

  it('handles different bus capacities correctly', () => {
    const smallBusTrip = {
      ...mockTrip,
      bus: {
        ...mockTrip.bus,
        capacity: 8
      }
    };

    render(
      <SeatMap 
        trip={smallBusTrip} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    // Should have seats 1-8
    for (let i = 1; i <= 8; i++) {
      expect(screen.getByTitle(new RegExp(`Seat ${i}`))).toBeInTheDocument();
    }

    // Should not have seat 9
    expect(screen.queryByTitle(new RegExp('Seat 9'))).not.toBeInTheDocument();
  });

  it('handles empty occupied seats array', () => {
    const tripWithNoOccupiedSeats = {
      ...mockTrip,
      occupied_seats: []
    };

    render(
      <SeatMap 
        trip={tripWithNoOccupiedSeats} 
        selectedSeats={[]} 
        onSeatSelect={mockOnSeatSelect} 
      />
    );

    // All seats should be available
    const seat1 = screen.getByTitle('Seat 1A - available');
    expect(seat1).not.toBeDisabled();
  });
});
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import TripResults from '../TripResults';

const mockTrips = [
  {
    id: '1',
    departure_time: '2024-12-25T10:00:00Z',
    arrival_time: '2024-12-25T14:00:00Z',
    estimated_duration: 240,
    fare: 50.00,
    available_seats: 15,
    origin_terminal: { name: 'Central Terminal', city: 'New York' },
    destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
    bus: {
      model: 'Mercedes Sprinter',
      license_plate: 'ABC-123',
      amenities: ['WiFi', 'AC', 'USB Charging']
    }
  },
  {
    id: '2',
    departure_time: '2024-12-25T12:00:00Z',
    arrival_time: '2024-12-25T16:30:00Z',
    estimated_duration: 270,
    fare: 75.00,
    available_seats: 0,
    origin_terminal: { name: 'Central Terminal', city: 'New York' },
    destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
    bus: {
      model: 'Volvo Coach',
      license_plate: 'XYZ-789',
      amenities: ['WiFi', 'Reclining Seats']
    }
  },
  {
    id: '3',
    departure_time: '2024-12-25T08:00:00Z',
    arrival_time: '2024-12-25T11:30:00Z',
    estimated_duration: 210,
    fare: 35.00,
    available_seats: 8,
    origin_terminal: { name: 'Central Terminal', city: 'New York' },
    destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
    bus: {
      model: 'Ford Transit',
      license_plate: 'DEF-456',
      amenities: ['AC']
    }
  }
];

describe('TripResults', () => {
  const mockOnSelectTrip = vi.fn();
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state', () => {
    render(<TripResults trips={[]} loading={true} onSelectTrip={mockOnSelectTrip} />);

    expect(screen.getByText('Searching for trips...')).toBeInTheDocument();
    expect(screen.getByRole('generic', { name: /loading/i })).toBeInTheDocument();
  });

  it('shows empty state when no trips found', () => {
    render(<TripResults trips={[]} loading={false} onSelectTrip={mockOnSelectTrip} />);

    expect(screen.getByText('No trips found')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your search criteria or selecting different dates.')).toBeInTheDocument();
  });

  it('displays trip results correctly', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    expect(screen.getByText('3 trips found')).toBeInTheDocument();

    // Check first trip details
    expect(screen.getByText('10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('2:00 PM')).toBeInTheDocument();
    expect(screen.getByText('4h 0m')).toBeInTheDocument();
    expect(screen.getByText('$50.00')).toBeInTheDocument();
    expect(screen.getByText('15 seats left')).toBeInTheDocument();
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.getByText('(ABC-123)')).toBeInTheDocument();

    // Check amenities
    expect(screen.getByText('WiFi')).toBeInTheDocument();
    expect(screen.getByText('AC')).toBeInTheDocument();
    expect(screen.getByText('USB Charging')).toBeInTheDocument();
  });

  it('shows fully booked trips correctly', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const fullyBookedTrip = screen.getByText('0 seats left');
    expect(fullyBookedTrip).toBeInTheDocument();
    expect(fullyBookedTrip).toHaveClass('full');

    const fullyBookedButton = screen.getByText('Fully Booked');
    expect(fullyBookedButton).toBeDisabled();
  });

  it('calls onSelectTrip when select button is clicked', async () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const selectButtons = screen.getAllByText('Select Seats');
    await user.click(selectButtons[0]);

    expect(mockOnSelectTrip).toHaveBeenCalledWith(mockTrips[0]);
  });

  it('sorts trips by departure time by default', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const times = screen.getAllByText(/\d{1,2}:\d{2} [AP]M/);
    // Should be sorted by departure time: 8:00 AM, 10:00 AM, 12:00 PM
    expect(times[0]).toHaveTextContent('8:00 AM');
    expect(times[2]).toHaveTextContent('10:00 AM');
    expect(times[4]).toHaveTextContent('12:00 PM');
  });

  it('sorts trips by price when price sort is selected', async () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const sortSelect = screen.getByLabelText('Sort by:');
    await user.selectOptions(sortSelect, 'price_low');

    // Should be sorted by price: $35.00, $50.00, $75.00
    const prices = screen.getAllByText(/\$\d+\.\d{2}/);
    expect(prices[0]).toHaveTextContent('$35.00');
    expect(prices[1]).toHaveTextContent('$50.00');
    expect(prices[2]).toHaveTextContent('$75.00');
  });

  it('filters trips by availability', async () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const filterSelect = screen.getByLabelText('Filter:');
    await user.selectOptions(filterSelect, 'available');

    // Should show only available trips (2 out of 3)
    expect(screen.getByText('2 trips found')).toBeInTheDocument();
    expect(screen.queryByText('Fully Booked')).not.toBeInTheDocument();
  });

  it('filters trips by price range', async () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const minPriceInput = screen.getByDisplayValue('0');
    const maxPriceInput = screen.getByDisplayValue('1000');

    await user.clear(minPriceInput);
    await user.type(minPriceInput, '40');
    await user.clear(maxPriceInput);
    await user.type(maxPriceInput, '60');

    // Should show only trips within price range ($50.00)
    expect(screen.getByText('1 trips found')).toBeInTheDocument();
    expect(screen.getByText('$50.00')).toBeInTheDocument();
    expect(screen.queryByText('$35.00')).not.toBeInTheDocument();
    expect(screen.queryByText('$75.00')).not.toBeInTheDocument();
  });

  it('formats time correctly', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    // Check various time formats
    expect(screen.getByText('8:00 AM')).toBeInTheDocument();
    expect(screen.getByText('10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('12:00 PM')).toBeInTheDocument();
    expect(screen.getByText('2:00 PM')).toBeInTheDocument();
    expect(screen.getByText('4:30 PM')).toBeInTheDocument();
  });

  it('formats duration correctly', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    expect(screen.getByText('3h 30m')).toBeInTheDocument(); // 210 minutes
    expect(screen.getByText('4h 0m')).toBeInTheDocument();  // 240 minutes
    expect(screen.getByText('4h 30m')).toBeInTheDocument(); // 270 minutes
  });

  it('formats price correctly', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    expect(screen.getByText('$35.00')).toBeInTheDocument();
    expect(screen.getByText('$50.00')).toBeInTheDocument();
    expect(screen.getByText('$75.00')).toBeInTheDocument();
    
    // Check "per person" text
    const perPersonTexts = screen.getAllByText('per person');
    expect(perPersonTexts).toHaveLength(3);
  });

  it('handles trips without amenities', () => {
    const tripsWithoutAmenities = [{
      ...mockTrips[0],
      bus: {
        ...mockTrips[0].bus,
        amenities: null
      }
    }];

    render(<TripResults trips={tripsWithoutAmenities} loading={false} onSelectTrip={mockOnSelectTrip} />);

    // Should not crash and should still display other trip information
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.getByText('(ABC-123)')).toBeInTheDocument();
  });

  it('shows correct seat availability colors', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const availableSeats = screen.getByText('15 seats left');
    expect(availableSeats).not.toHaveClass('full');

    const fullSeats = screen.getByText('0 seats left');
    expect(fullSeats).toHaveClass('full');
  });

  it('disables select button for fully booked trips', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const selectButtons = screen.getAllByRole('button');
    const fullyBookedButton = selectButtons.find(button => button.textContent === 'Fully Booked');
    
    expect(fullyBookedButton).toBeDisabled();
  });

  it('enables select button for available trips', () => {
    render(<TripResults trips={mockTrips} loading={false} onSelectTrip={mockOnSelectTrip} />);

    const selectButtons = screen.getAllByText('Select Seats');
    selectButtons.forEach(button => {
      expect(button).not.toBeDisabled();
    });
  });
});
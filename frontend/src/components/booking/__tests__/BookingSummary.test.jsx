import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import BookingSummary from '../BookingSummary';

const mockTrip = {
  id: '1',
  departure_time: '2024-12-25T10:00:00Z',
  arrival_time: '2024-12-25T14:00:00Z',
  estimated_duration: 240,
  fare: 50.00,
  origin_terminal: { name: 'Central Terminal', city: 'New York' },
  destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
  bus: {
    model: 'Mercedes Sprinter',
    license_plate: 'ABC-123',
    amenities: ['WiFi', 'AC', 'USB Charging']
  }
};

describe('BookingSummary', () => {
  const mockOnEdit = vi.fn();
  const mockOnConfirm = vi.fn();
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no trip is provided', () => {
    render(
      <BookingSummary 
        trip={null}
        selectedSeats={[]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Booking Summary')).toBeInTheDocument();
    expect(screen.getByText('Please select a trip and seats to see booking summary')).toBeInTheDocument();
  });

  it('displays trip information correctly', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Central Terminal → Airport Terminal')).toBeInTheDocument();
    expect(screen.getByText('New York to Los Angeles')).toBeInTheDocument();
  });

  it('displays journey details correctly', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Departure')).toBeInTheDocument();
    expect(screen.getByText('10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('Tuesday, December 25, 2024')).toBeInTheDocument();

    expect(screen.getByText('Duration')).toBeInTheDocument();
    expect(screen.getByText('4h 0m')).toBeInTheDocument();

    expect(screen.getByText('Arrival')).toBeInTheDocument();
    expect(screen.getByText('2:00 PM')).toBeInTheDocument();
  });

  it('displays bus information correctly', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Bus Information')).toBeInTheDocument();
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.getByText('(ABC-123)')).toBeInTheDocument();

    expect(screen.getByText('Amenities:')).toBeInTheDocument();
    expect(screen.getByText('WiFi')).toBeInTheDocument();
    expect(screen.getByText('AC')).toBeInTheDocument();
    expect(screen.getByText('USB Charging')).toBeInTheDocument();
  });

  it('displays selected seats correctly', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 3, 5]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Selected Seats')).toBeInTheDocument();
    expect(screen.getByText('Seat 1')).toBeInTheDocument();
    expect(screen.getByText('Seat 3')).toBeInTheDocument();
    expect(screen.getByText('Seat 5')).toBeInTheDocument();

    // Each seat should show the price
    const seatPrices = screen.getAllByText('$50.00');
    expect(seatPrices).toHaveLength(4); // 3 seats + 1 in price breakdown
  });

  it('shows no seats message when no seats selected', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('No seats selected')).toBeInTheDocument();
  });

  it('calculates price breakdown correctly', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Price Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Subtotal (2 seats)')).toBeInTheDocument();
    expect(screen.getByText('$100.00')).toBeInTheDocument(); // 2 * $50.00

    expect(screen.getByText('Tax (10%)')).toBeInTheDocument();
    expect(screen.getByText('$10.00')).toBeInTheDocument(); // 10% of $100.00

    expect(screen.getByText('Total Amount')).toBeInTheDocument();
    expect(screen.getByText('$110.00')).toBeInTheDocument(); // $100.00 + $10.00
  });

  it('handles single seat correctly in price breakdown', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Subtotal (1 seat)')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', async () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    const editButton = screen.getByText('Edit Selection');
    await user.click(editButton);

    expect(mockOnEdit).toHaveBeenCalledTimes(1);
  });

  it('calls onConfirm with correct data when proceed button is clicked', async () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    const proceedButton = screen.getByText('Proceed to Payment');
    await user.click(proceedButton);

    expect(mockOnConfirm).toHaveBeenCalledWith({
      trip: mockTrip,
      selectedSeats: [1, 2],
      totalAmount: 110.00,
      subtotal: 100.00,
      tax: 10.00
    });
  });

  it('disables proceed button when no seats selected', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    const proceedButton = screen.getByText('Proceed to Payment');
    expect(proceedButton).toBeDisabled();
  });

  it('disables proceed button when loading', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
        loading={true}
      />
    );

    const proceedButton = screen.getByText('Processing...');
    expect(proceedButton).toBeDisabled();
  });

  it('displays terms and conditions links', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('By proceeding, you agree to our')).toBeInTheDocument();
    
    const termsLink = screen.getByText('Terms of Service');
    expect(termsLink).toHaveAttribute('href', '/terms');
    expect(termsLink).toHaveAttribute('target', '_blank');

    const privacyLink = screen.getByText('Privacy Policy');
    expect(privacyLink).toHaveAttribute('href', '/privacy');
    expect(privacyLink).toHaveAttribute('target', '_blank');
  });

  it('handles trip without amenities', () => {
    const tripWithoutAmenities = {
      ...mockTrip,
      bus: {
        ...mockTrip.bus,
        amenities: null
      }
    };

    render(
      <BookingSummary 
        trip={tripWithoutAmenities}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Bus Information')).toBeInTheDocument();
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.queryByText('Amenities:')).not.toBeInTheDocument();
  });

  it('handles trip with empty amenities array', () => {
    const tripWithEmptyAmenities = {
      ...mockTrip,
      bus: {
        ...mockTrip.bus,
        amenities: []
      }
    };

    render(
      <BookingSummary 
        trip={tripWithEmptyAmenities}
        selectedSeats={[1, 2]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Bus Information')).toBeInTheDocument();
    expect(screen.getByText('Mercedes Sprinter')).toBeInTheDocument();
    expect(screen.queryByText('Amenities:')).not.toBeInTheDocument();
  });

  it('formats currency correctly', () => {
    render(
      <BookingSummary 
        trip={mockTrip}
        selectedSeats={[1]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    // Check that all prices are formatted as USD currency
    expect(screen.getByText('$50.00')).toBeInTheDocument(); // Seat price
    expect(screen.getByText('$5.00')).toBeInTheDocument();  // Tax
    expect(screen.getByText('$55.00')).toBeInTheDocument(); // Total
  });

  it('calculates tax correctly for different amounts', () => {
    const expensiveTrip = {
      ...mockTrip,
      fare: 100.00
    };

    render(
      <BookingSummary 
        trip={expensiveTrip}
        selectedSeats={[1, 2, 3]}
        onEdit={mockOnEdit}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('$300.00')).toBeInTheDocument(); // Subtotal: 3 * $100.00
    expect(screen.getByText('$30.00')).toBeInTheDocument();  // Tax: 10% of $300.00
    expect(screen.getByText('$330.00')).toBeInTheDocument(); // Total: $300.00 + $30.00
  });
});
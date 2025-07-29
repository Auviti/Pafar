import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import BookingHistory from '../BookingHistory';
import { bookingService } from '../../../services/booking';
import { paymentService } from '../../../services/payment';

// Mock the dependencies
vi.mock('../../../services/booking');
vi.mock('../../../services/payment');

const mockBookings = [
  {
    id: '1',
    booking_reference: 'BK001',
    status: 'confirmed',
    payment_status: 'completed',
    total_amount: 25.00,
    seat_numbers: [1, 2],
    created_at: '2024-01-15T10:00:00Z',
    trip: {
      id: 'trip1',
      departure_time: '2024-02-01T14:00:00Z',
      route: {
        origin_terminal: { name: 'New York' },
        destination_terminal: { name: 'Boston' }
      },
      bus: {
        license_plate: 'ABC123',
        model: 'Mercedes Sprinter'
      },
      driver: {
        first_name: 'John',
        last_name: 'Driver'
      }
    }
  },
  {
    id: '2',
    booking_reference: 'BK002',
    status: 'completed',
    payment_status: 'completed',
    total_amount: 30.00,
    seat_numbers: [5],
    created_at: '2024-01-10T09:00:00Z',
    trip: {
      id: 'trip2',
      departure_time: '2024-01-20T16:00:00Z',
      route: {
        origin_terminal: { name: 'Boston' },
        destination_terminal: { name: 'Philadelphia' }
      },
      bus: {
        license_plate: 'XYZ789',
        model: 'Volvo Coach'
      }
    }
  },
  {
    id: '3',
    booking_reference: 'BK003',
    status: 'cancelled',
    payment_status: 'refunded',
    total_amount: 20.00,
    seat_numbers: [3],
    created_at: '2024-01-05T11:00:00Z',
    trip: {
      id: 'trip3',
      departure_time: '2024-01-25T12:00:00Z',
      route: {
        origin_terminal: { name: 'Philadelphia' },
        destination_terminal: { name: 'Washington DC' }
      },
      bus: {
        license_plate: 'DEF456',
        model: 'Ford Transit'
      }
    }
  }
];

describe('BookingHistory', () => {
  beforeEach(() => {
    bookingService.getUserBookings.mockResolvedValue(mockBookings);
    paymentService.getReceipt.mockResolvedValue('mock-pdf-data');
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders booking history with all bookings', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('My Bookings')).toBeInTheDocument();
    });
    
    expect(screen.getByText('New York → Boston')).toBeInTheDocument();
    expect(screen.getByText('Boston → Philadelphia')).toBeInTheDocument();
    expect(screen.getByText('Philadelphia → Washington DC')).toBeInTheDocument();
    
    expect(screen.getByText('BK001')).toBeInTheDocument();
    expect(screen.getByText('BK002')).toBeInTheDocument();
    expect(screen.getByText('BK003')).toBeInTheDocument();
  });

  it('filters bookings by status', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('My Bookings')).toBeInTheDocument();
    });
    
    // Filter by confirmed status
    const filterSelect = screen.getByDisplayValue('All Bookings');
    fireEvent.change(filterSelect, { target: { value: 'confirmed' } });
    
    expect(screen.getByText('New York → Boston')).toBeInTheDocument();
    expect(screen.queryByText('Boston → Philadelphia')).not.toBeInTheDocument();
    expect(screen.queryByText('Philadelphia → Washington DC')).not.toBeInTheDocument();
  });

  it('displays correct status badges', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Confirmed')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Cancelled')).toBeInTheDocument();
    });
  });

  it('displays payment status badges', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Payment: completed')).toHaveLength(2);
      expect(screen.getByText('Payment: refunded')).toBeInTheDocument();
    });
  });

  it('shows download receipt button for completed payments', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getAllByText('Download Receipt')).toHaveLength(2);
    });
  });

  it('shows cancel button for cancellable bookings', async () => {
    // Mock a future booking that can be cancelled
    const futureBooking = {
      ...mockBookings[0],
      trip: {
        ...mockBookings[0].trip,
        departure_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours from now
      }
    };
    
    bookingService.getUserBookings.mockResolvedValue([futureBooking]);
    
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Cancel Booking')).toBeInTheDocument();
    });
  });

  it('does not show cancel button for past or cancelled bookings', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.queryByText('Cancel Booking')).not.toBeInTheDocument();
    });
  });

  it('opens cancellation modal when cancel button is clicked', async () => {
    // Mock a future booking that can be cancelled
    const futureBooking = {
      ...mockBookings[0],
      trip: {
        ...mockBookings[0].trip,
        departure_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      }
    };
    
    bookingService.getUserBookings.mockResolvedValue([futureBooking]);
    
    render(<BookingHistory />);
    
    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel Booking');
      fireEvent.click(cancelButton);
    });
    
    expect(screen.getByText('Cancel Booking')).toBeInTheDocument();
    expect(screen.getByText('Booking Details')).toBeInTheDocument();
  });

  it('handles download receipt', async () => {
    // Mock URL.createObjectURL and related methods
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    const mockLink = {
      click: vi.fn(),
      download: '',
      href: ''
    };
    document.createElement = vi.fn(() => mockLink);
    document.body.appendChild = vi.fn();
    document.body.removeChild = vi.fn();
    
    render(<BookingHistory />);
    
    await waitFor(() => {
      const downloadButton = screen.getAllByText('Download Receipt')[0];
      fireEvent.click(downloadButton);
    });
    
    expect(paymentService.getReceipt).toHaveBeenCalled();
  });

  it('displays empty state when no bookings', async () => {
    bookingService.getUserBookings.mockResolvedValue([]);
    
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('No bookings found')).toBeInTheDocument();
      expect(screen.getByText('Start by booking your first trip!')).toBeInTheDocument();
    });
  });

  it('displays filtered empty state', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      const filterSelect = screen.getByDisplayValue('All Bookings');
      fireEvent.change(filterSelect, { target: { value: 'pending' } });
    });
    
    expect(screen.getByText('No pending bookings found')).toBeInTheDocument();
    expect(screen.getByText('Try changing the filter to see other bookings.')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    bookingService.getUserBookings.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<BookingHistory />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error state', async () => {
    bookingService.getUserBookings.mockRejectedValue(new Error('Failed to fetch bookings'));
    
    render(<BookingHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Error: Failed to fetch bookings')).toBeInTheDocument();
    });
  });

  it('displays booking details correctly', async () => {
    render(<BookingHistory />);
    
    await waitFor(() => {
      // Check seat information
      expect(screen.getByText('1, 2')).toBeInTheDocument();
      expect(screen.getByText('2 seats')).toBeInTheDocument();
      expect(screen.getByText('1 seat')).toBeInTheDocument();
      
      // Check amounts
      expect(screen.getByText('$25')).toBeInTheDocument();
      expect(screen.getByText('$30')).toBeInTheDocument();
      expect(screen.getByText('$20')).toBeInTheDocument();
      
      // Check bus and driver info
      expect(screen.getByText('ABC123 (Mercedes Sprinter)')).toBeInTheDocument();
      expect(screen.getByText('John Driver')).toBeInTheDocument();
    });
  });
});
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import TripStatusDisplay from '../TripStatusDisplay';
import { trackingService } from '../../../services/tracking';
import useWebSocket from '../../../hooks/useWebSocket';

// Mock the services and hooks
vi.mock('../../../services/tracking');
vi.mock('../../../hooks/useWebSocket');

describe('TripStatusDisplay', () => {
  const mockTripId = 'test-trip-123';
  const mockTripStatus = {
    status: 'in_transit',
    scheduled_departure: '2024-01-15T10:00:00Z',
    scheduled_arrival: '2024-01-15T14:00:00Z',
    updated_at: '2024-01-15T12:00:00Z',
  };
  
  const mockEta = {
    estimated_arrival: '2024-01-15T14:15:00Z',
    remaining_minutes: 135,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock tracking service
    trackingService.getTripStatus.mockResolvedValue(mockTripStatus);
    trackingService.getTripETA.mockResolvedValue(mockEta);
    
    // Mock WebSocket hook
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()), // Return unsubscribe function
      isConnected: true,
    });
  });

  it('renders loading state initially', () => {
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    // Check for loading animation
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('displays trip status after loading', async () => {
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('🛣️ In Transit')).toBeInTheDocument();
      expect(screen.getByText('Bus is on the way to destination')).toBeInTheDocument();
    });
  });

  it('displays connection status', async () => {
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Live')).toBeInTheDocument();
    });
  });

  it('shows offline status when disconnected', async () => {
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()),
      isConnected: false,
    });

    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  it('displays progress indicator', async () => {
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Scheduled')).toBeInTheDocument();
      expect(screen.getByText('Boarding')).toBeInTheDocument();
      expect(screen.getByText('Departed')).toBeInTheDocument();
      expect(screen.getByText('In Transit')).toBeInTheDocument();
      expect(screen.getByText('Approaching')).toBeInTheDocument();
      expect(screen.getByText('Arrived')).toBeInTheDocument();
    });
  });

  it('displays trip details', async () => {
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Departure:')).toBeInTheDocument();
      expect(screen.getByText('Arrival:')).toBeInTheDocument();
      expect(screen.getByText('ETA:')).toBeInTheDocument();
      expect(screen.getByText('Remaining:')).toBeInTheDocument();
    });
  });

  it('shows delay warning for delayed trips', async () => {
    const delayedStatus = {
      ...mockTripStatus,
      status: 'delayed',
      delay_minutes: 30,
    };
    
    trackingService.getTripStatus.mockResolvedValue(delayedStatus);
    
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('⏰ Delayed')).toBeInTheDocument();
      expect(screen.getByText('Trip is delayed by 30 minutes')).toBeInTheDocument();
    });
  });

  it('handles cancelled trips', async () => {
    const cancelledStatus = {
      ...mockTripStatus,
      status: 'cancelled',
    };
    
    trackingService.getTripStatus.mockResolvedValue(cancelledStatus);
    
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('❌ Cancelled')).toBeInTheDocument();
      expect(screen.getByText('Trip has been cancelled')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    trackingService.getTripStatus.mockRejectedValue(new Error('API Error'));
    
    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load trip status')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('subscribes to WebSocket updates', async () => {
    const mockSubscribe = vi.fn(() => vi.fn());
    useWebSocket.mockReturnValue({
      subscribe: mockSubscribe,
      isConnected: true,
    });

    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(mockSubscribe).toHaveBeenCalledWith('trip_status_update', expect.any(Function));
      expect(mockSubscribe).toHaveBeenCalledWith('eta_update', expect.any(Function));
    });
  });

  it('updates status from WebSocket', async () => {
    const mockSubscribe = vi.fn();
    let statusUpdateCallback;
    
    mockSubscribe.mockImplementation((event, callback) => {
      if (event === 'trip_status_update') {
        statusUpdateCallback = callback;
      }
      return vi.fn();
    });
    
    useWebSocket.mockReturnValue({
      subscribe: mockSubscribe,
      isConnected: true,
    });

    render(<TripStatusDisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('🛣️ In Transit')).toBeInTheDocument();
    });

    // Simulate WebSocket status update
    if (statusUpdateCallback) {
      statusUpdateCallback({
        trip_id: mockTripId,
        status: 'approaching',
        timestamp: new Date().toISOString(),
      });
    }

    await waitFor(() => {
      expect(screen.getByText('📍 Approaching')).toBeInTheDocument();
    });
  });

  it('applies custom className', () => {
    const customClass = 'custom-status-class';
    render(<TripStatusDisplay tripId={mockTripId} className={customClass} />);
    
    const statusContainer = document.querySelector('.animate-pulse');
    expect(statusContainer.closest('div')).toHaveClass(customClass);
  });
});
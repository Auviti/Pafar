import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ETADisplay from '../ETADisplay';
import { trackingService } from '../../../services/tracking';
import useWebSocket from '../../../hooks/useWebSocket';

// Mock the services and hooks
vi.mock('../../../services/tracking');
vi.mock('../../../hooks/useWebSocket');

describe('ETADisplay', () => {
  const mockTripId = 'test-trip-123';
  const mockEta = {
    estimated_arrival: '2024-01-15T14:15:00Z',
    scheduled_arrival: '2024-01-15T14:00:00Z',
    remaining_minutes: 135,
    remaining_distance: 45.5,
    average_speed: 65,
    traffic_condition: 'moderate',
    confidence_level: 85,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock current time to make tests predictable
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    
    // Mock tracking service
    trackingService.getTripETA.mockResolvedValue(mockEta);
    
    // Mock WebSocket hook
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()), // Return unsubscribe function
      isConnected: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders loading state initially', () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    // Check for loading animation
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('displays ETA after loading', async () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(trackingService.getTripETA).toHaveBeenCalledWith(mockTripId);
    });
    
    await waitFor(() => {
      expect(screen.getByText('🕐 Estimated Arrival')).toBeInTheDocument();
      expect(screen.getByText('2:15 PM')).toBeInTheDocument(); // 14:15 formatted
    });
  });

  it('displays connection status', async () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Live')).toBeInTheDocument();
    });
  });

  it('shows offline status when disconnected', async () => {
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()),
      isConnected: false,
    });

    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  it('displays delay status for delayed trips', async () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Running 15 minutes late')).toBeInTheDocument();
    });
  });

  it('displays early status for early trips', async () => {
    const earlyEta = {
      ...mockEta,
      estimated_arrival: '2024-01-15T13:45:00Z', // 15 minutes early
    };
    
    trackingService.getTripETA.mockResolvedValue(earlyEta);
    
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Running 15 minutes early')).toBeInTheDocument();
    });
  });

  it('displays on-time status', async () => {
    const onTimeEta = {
      ...mockEta,
      estimated_arrival: '2024-01-15T14:02:00Z', // 2 minutes late (within tolerance)
    };
    
    trackingService.getTripETA.mockResolvedValue(onTimeEta);
    
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('On schedule')).toBeInTheDocument();
    });
  });

  it('displays trip details', async () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Scheduled:')).toBeInTheDocument();
      expect(screen.getByText('Distance:')).toBeInTheDocument();
      expect(screen.getByText('45.5 km')).toBeInTheDocument();
      expect(screen.getByText('Avg Speed:')).toBeInTheDocument();
      expect(screen.getByText('65 km/h')).toBeInTheDocument();
      expect(screen.getByText('Traffic:')).toBeInTheDocument();
      expect(screen.getByText('Moderate')).toBeInTheDocument();
    });
  });

  it('displays confidence level', async () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Accuracy:')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('shows time until arrival', async () => {
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('in 2h 15m')).toBeInTheDocument();
    });
  });

  it('shows arrived status when ETA is in the past', async () => {
    const pastEta = {
      ...mockEta,
      estimated_arrival: '2024-01-15T11:30:00Z', // 30 minutes ago
    };
    
    trackingService.getTripETA.mockResolvedValue(pastEta);
    
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Arrived or arriving now')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    trackingService.getTripETA.mockRejectedValue(new Error('API Error'));
    
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('ETA unavailable')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('subscribes to WebSocket updates', async () => {
    const mockSubscribe = vi.fn(() => vi.fn());
    useWebSocket.mockReturnValue({
      subscribe: mockSubscribe,
      isConnected: true,
    });

    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(mockSubscribe).toHaveBeenCalledWith('eta_update', expect.any(Function));
    });
  });

  it('updates ETA from WebSocket', async () => {
    const mockSubscribe = vi.fn();
    let etaUpdateCallback;
    
    mockSubscribe.mockImplementation((event, callback) => {
      if (event === 'eta_update') {
        etaUpdateCallback = callback;
      }
      return vi.fn();
    });
    
    useWebSocket.mockReturnValue({
      subscribe: mockSubscribe,
      isConnected: true,
    });

    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('02:15 PM')).toBeInTheDocument();
    });

    // Simulate WebSocket ETA update
    if (etaUpdateCallback) {
      etaUpdateCallback({
        trip_id: mockTripId,
        eta_data: {
          ...mockEta,
          estimated_arrival: '2024-01-15T14:30:00Z',
        },
      });
    }

    await waitFor(() => {
      expect(screen.getByText('02:30 PM')).toBeInTheDocument();
    });
  });

  it('displays traffic condition colors correctly', async () => {
    const heavyTrafficEta = {
      ...mockEta,
      traffic_condition: 'heavy',
    };
    
    trackingService.getTripETA.mockResolvedValue(heavyTrafficEta);
    
    render(<ETADisplay tripId={mockTripId} />);
    
    await waitFor(() => {
      const trafficElement = screen.getByText('Heavy');
      expect(trafficElement).toHaveClass('text-red-600');
    });
  });

  it('applies custom className', () => {
    const customClass = 'custom-eta-class';
    render(<ETADisplay tripId={mockTripId} className={customClass} />);
    
    const etaContainer = document.querySelector('.animate-pulse');
    expect(etaContainer.closest('div')).toHaveClass(customClass);
  });
});
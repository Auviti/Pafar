import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import TripTrackingMap from '../TripTrackingMap';
import { trackingService } from '../../../services/tracking';
import useWebSocket from '../../../hooks/useWebSocket';

// Mock the services and hooks
vi.mock('../../../services/tracking');
vi.mock('../../../hooks/useWebSocket');

// Mock Google Maps
const mockMap = {
  panTo: vi.fn(),
  setCenter: vi.fn(),
};

const mockMarker = {
  setPosition: vi.fn(),
  setMap: vi.fn(),
};

const mockPolyline = {
  setMap: vi.fn(),
};

global.window.google = {
  maps: {
    Map: vi.fn(() => mockMap),
    Marker: vi.fn(() => mockMarker),
    Polyline: vi.fn(() => mockPolyline),
    MapTypeId: {
      ROADMAP: 'roadmap',
    },
    Size: vi.fn(),
    Point: vi.fn(),
  },
};

describe('TripTrackingMap', () => {
  const mockTripId = 'test-trip-123';
  const mockTrackingData = {
    current_location: {
      latitude: 40.7128,
      longitude: -74.0060,
      speed: 45,
    },
  };
  
  const mockRouteData = {
    origin_coordinates: { lat: 40.7128, lng: -74.0060 },
    destination_coordinates: { lat: 40.7589, lng: -73.9851 },
    origin_terminal: 'Terminal A',
    destination_terminal: 'Terminal B',
    route_coordinates: [
      { lat: 40.7128, lng: -74.0060 },
      { lat: 40.7589, lng: -73.9851 },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock tracking service
    trackingService.getTripTracking.mockResolvedValue(mockTrackingData);
    trackingService.getTripRoute.mockResolvedValue(mockRouteData);
    
    // Mock WebSocket hook
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()), // Return unsubscribe function
      isConnected: true,
    });

    // Mock environment variable
    import.meta.env.VITE_GOOGLE_MAPS_API_KEY = 'test-api-key';
    
    // Mock document.head.appendChild to simulate script loading
    const originalAppendChild = document.head.appendChild;
    document.head.appendChild = vi.fn((script) => {
      if (script.src && script.src.includes('maps.googleapis.com')) {
        // Simulate successful script load
        setTimeout(() => script.onload && script.onload(), 0);
      }
      return originalAppendChild.call(document.head, script);
    });
  });

  it('renders loading state initially', () => {
    render(<TripTrackingMap tripId={mockTripId} />);
    
    expect(screen.getByText('Loading map...')).toBeInTheDocument();
  });

  it('renders map after loading', async () => {
    render(<TripTrackingMap tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(trackingService.getTripTracking).toHaveBeenCalledWith(mockTripId);
      expect(trackingService.getTripRoute).toHaveBeenCalledWith(mockTripId);
    });
  });

  it('displays connection status', async () => {
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()),
      isConnected: true,
    });

    render(<TripTrackingMap tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Live')).toBeInTheDocument();
    });
  });

  it('displays offline status when disconnected', async () => {
    useWebSocket.mockReturnValue({
      subscribe: vi.fn(() => vi.fn()),
      isConnected: false,
    });

    render(<TripTrackingMap tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  it('displays current location info', async () => {
    render(<TripTrackingMap tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Current Location')).toBeInTheDocument();
      expect(screen.getByText('40.712800, -74.006000')).toBeInTheDocument();
      expect(screen.getByText('Speed: 45 km/h')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    trackingService.getTripTracking.mockRejectedValue(new Error('API Error'));
    
    render(<TripTrackingMap tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load map')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('subscribes to WebSocket updates', async () => {
    const mockSubscribe = vi.fn(() => vi.fn());
    useWebSocket.mockReturnValue({
      subscribe: mockSubscribe,
      isConnected: true,
    });

    render(<TripTrackingMap tripId={mockTripId} />);
    
    await waitFor(() => {
      expect(mockSubscribe).toHaveBeenCalledWith('location_update', expect.any(Function));
      expect(mockSubscribe).toHaveBeenCalledWith('trip_status_update', expect.any(Function));
    });
  });

  it('applies custom className', () => {
    const customClass = 'custom-map-class';
    render(<TripTrackingMap tripId={mockTripId} className={customClass} />);
    
    const mapContainer = screen.getByText('Loading map...').closest('div');
    expect(mapContainer).toHaveClass(customClass);
  });
});
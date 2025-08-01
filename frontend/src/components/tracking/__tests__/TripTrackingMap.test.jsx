import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TripTrackingMap from '../TripTrackingMap';

// Mock Google Maps
const mockMap = {
  setCenter: vi.fn(),
  setZoom: vi.fn(),
  panTo: vi.fn(),
};

const mockMarker = {
  setPosition: vi.fn(),
  setMap: vi.fn(),
  setIcon: vi.fn(),
};

const mockDirectionsService = {
  route: vi.fn(),
};

const mockDirectionsRenderer = {
  setDirections: vi.fn(),
  setMap: vi.fn(),
};

global.google = {
  maps: {
    Map: vi.fn(() => mockMap),
    Marker: vi.fn(() => mockMarker),
    DirectionsService: vi.fn(() => mockDirectionsService),
    DirectionsRenderer: vi.fn(() => mockDirectionsRenderer),
    LatLng: vi.fn((lat, lng) => ({ lat, lng })),
    TravelMode: { DRIVING: 'DRIVING' },
    DirectionsStatus: { OK: 'OK' },
    event: {
      addListener: vi.fn(),
      removeListener: vi.fn(),
    },
  },
};

// Mock WebSocket
const mockWebSocket = {
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  close: vi.fn(),
  send: vi.fn(),
  readyState: WebSocket.OPEN,
};

global.WebSocket = vi.fn(() => mockWebSocket);

const mockTrip = {
  id: '1',
  route: {
    origin_terminal: {
      id: '1',
      name: 'Origin Terminal',
      latitude: 40.7128,
      longitude: -74.0060,
    },
    destination_terminal: {
      id: '2',
      name: 'Destination Terminal',
      latitude: 40.7589,
      longitude: -73.9851,
    },
  },
  bus: {
    id: '1',
    license_plate: 'ABC-123',
    model: 'Mercedes Sprinter',
  },
  driver: {
    id: '1',
    first_name: 'John',
    last_name: 'Driver',
  },
  departure_time: '2024-01-01T10:00:00Z',
  status: 'in_progress',
};

const mockCurrentLocation = {
  latitude: 40.7300,
  longitude: -73.9950,
  speed: 45.5,
  heading: 180,
  recorded_at: '2024-01-01T10:30:00Z',
};

const defaultProps = {
  trip: mockTrip,
  currentLocation: mockCurrentLocation,
  showRoute: true,
  showTraffic: false,
  height: '400px',
};

describe('TripTrackingMap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders map container', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(screen.getByTestId('trip-tracking-map')).toBeInTheDocument();
    expect(screen.getByTestId('map-container')).toBeInTheDocument();
  });

  it('initializes Google Map with correct options', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(global.google.maps.Map).toHaveBeenCalledWith(
      expect.any(Element),
      expect.objectContaining({
        zoom: 12,
        center: { lat: 40.7300, lng: -73.9950 },
        mapTypeId: 'roadmap',
      })
    );
  });

  it('creates markers for terminals and bus', () => {
    render(<TripTrackingMap {...defaultProps} />);

    // Should create 3 markers: origin, destination, and bus
    expect(global.google.maps.Marker).toHaveBeenCalledTimes(3);
  });

  it('displays trip information panel', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(screen.getByText('Trip ABC-123')).toBeInTheDocument();
    expect(screen.getByText('Driver: John Driver')).toBeInTheDocument();
    expect(screen.getByText('Origin Terminal')).toBeInTheDocument();
    expect(screen.getByText('Destination Terminal')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('shows current speed and heading', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(screen.getByText('45.5 mph')).toBeInTheDocument();
    expect(screen.getByText('Heading: 180°')).toBeInTheDocument();
  });

  it('updates bus marker position when location changes', () => {
    const { rerender } = render(<TripTrackingMap {...defaultProps} />);

    const newLocation = {
      ...mockCurrentLocation,
      latitude: 40.7400,
      longitude: -73.9900,
    };

    rerender(<TripTrackingMap {...defaultProps} currentLocation={newLocation} />);

    expect(mockMarker.setPosition).toHaveBeenCalledWith({ lat: 40.7400, lng: -73.9900 });
  });

  it('shows route when showRoute is true', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(global.google.maps.DirectionsService).toHaveBeenCalled();
    expect(mockDirectionsService.route).toHaveBeenCalledWith(
      expect.objectContaining({
        origin: { lat: 40.7128, lng: -74.0060 },
        destination: { lat: 40.7589, lng: -73.9851 },
        travelMode: 'DRIVING',
      }),
      expect.any(Function)
    );
  });

  it('hides route when showRoute is false', () => {
    render(<TripTrackingMap {...defaultProps} showRoute={false} />);

    expect(mockDirectionsRenderer.setMap).toHaveBeenCalledWith(null);
  });

  it('toggles traffic layer', async () => {
    const user = userEvent.setup();
    render(<TripTrackingMap {...defaultProps} />);

    const trafficToggle = screen.getByRole('button', { name: /show traffic/i });
    await user.click(trafficToggle);

    // Traffic layer should be enabled
    expect(screen.getByRole('button', { name: /hide traffic/i })).toBeInTheDocument();
  });

  it('centers map on bus location', async () => {
    const user = userEvent.setup();
    render(<TripTrackingMap {...defaultProps} />);

    const centerButton = screen.getByRole('button', { name: /center on bus/i });
    await user.click(centerButton);

    expect(mockMap.panTo).toHaveBeenCalledWith({ lat: 40.7300, lng: -73.9950 });
  });

  it('shows ETA information', () => {
    const propsWithETA = {
      ...defaultProps,
      estimatedArrival: '2024-01-01T12:00:00Z',
    };

    render(<TripTrackingMap {...propsWithETA} />);

    expect(screen.getByText(/ETA:/)).toBeInTheDocument();
    expect(screen.getByText('12:00 PM')).toBeInTheDocument();
  });

  it('handles missing current location', () => {
    const propsWithoutLocation = {
      ...defaultProps,
      currentLocation: null,
    };

    render(<TripTrackingMap {...propsWithoutLocation} />);

    expect(screen.getByText('Location not available')).toBeInTheDocument();
  });

  it('shows trip status with appropriate styling', () => {
    const propsWithDifferentStatus = {
      ...defaultProps,
      trip: {
        ...mockTrip,
        status: 'completed',
      },
    };

    render(<TripTrackingMap {...propsWithDifferentStatus} />);

    const statusElement = screen.getByText('Completed');
    expect(statusElement).toHaveClass('status-completed');
  });

  it('displays last update time', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(screen.getByText(/Last update:/)).toBeInTheDocument();
    expect(screen.getByText('10:30 AM')).toBeInTheDocument();
  });

  it('handles map loading error', () => {
    // Mock Google Maps to throw error
    global.google.maps.Map = vi.fn(() => {
      throw new Error('Map failed to load');
    });

    render(<TripTrackingMap {...defaultProps} />);

    expect(screen.getByText('Failed to load map')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('shows fullscreen toggle', async () => {
    const user = userEvent.setup();
    render(<TripTrackingMap {...defaultProps} />);

    const fullscreenButton = screen.getByRole('button', { name: /fullscreen/i });
    await user.click(fullscreenButton);

    expect(screen.getByTestId('trip-tracking-map')).toHaveClass('fullscreen');
  });

  it('displays distance traveled', () => {
    const propsWithDistance = {
      ...defaultProps,
      distanceTraveled: 15.5,
    };

    render(<TripTrackingMap {...propsWithDistance} />);

    expect(screen.getByText('15.5 km traveled')).toBeInTheDocument();
  });

  it('shows next stop information', () => {
    const propsWithNextStop = {
      ...defaultProps,
      nextStop: {
        name: 'Intermediate Terminal',
        eta: '2024-01-01T11:00:00Z',
      },
    };

    render(<TripTrackingMap {...propsWithNextStop} />);

    expect(screen.getByText('Next Stop: Intermediate Terminal')).toBeInTheDocument();
    expect(screen.getByText('ETA: 11:00 AM')).toBeInTheDocument();
  });

  it('handles WebSocket connection for real-time updates', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(global.WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('/ws/tracking/1')
    );
    expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));
  });

  it('cleans up WebSocket on unmount', () => {
    const { unmount } = render(<TripTrackingMap {...defaultProps} />);

    unmount();

    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('shows map controls', () => {
    render(<TripTrackingMap {...defaultProps} />);

    expect(screen.getByRole('button', { name: /zoom in/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /zoom out/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /center on bus/i })).toBeInTheDocument();
  });

  it('handles different map types', async () => {
    const user = userEvent.setup();
    render(<TripTrackingMap {...defaultProps} />);

    const mapTypeButton = screen.getByRole('button', { name: /satellite/i });
    await user.click(mapTypeButton);

    // Should switch to satellite view
    expect(screen.getByRole('button', { name: /roadmap/i })).toBeInTheDocument();
  });

  it('shows trip progress bar', () => {
    const propsWithProgress = {
      ...defaultProps,
      progress: 65,
    };

    render(<TripTrackingMap {...propsWithProgress} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '65');
    expect(screen.getByText('65% Complete')).toBeInTheDocument();
  });
});
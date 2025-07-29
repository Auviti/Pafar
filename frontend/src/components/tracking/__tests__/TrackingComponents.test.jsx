import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import TripTrackingMap from '../TripTrackingMap';
import TripStatusDisplay from '../TripStatusDisplay';
import ETADisplay from '../ETADisplay';
import NotificationCenter from '../NotificationCenter';
import TripHistory from '../TripHistory';

// Mock the services and hooks
vi.mock('../../../services/tracking', () => ({
  trackingService: {
    getTripTracking: vi.fn().mockRejectedValue(new Error('Mock error')),
    getTripRoute: vi.fn().mockRejectedValue(new Error('Mock error')),
    getTripStatus: vi.fn().mockRejectedValue(new Error('Mock error')),
    getTripETA: vi.fn().mockRejectedValue(new Error('Mock error')),
  }
}));

vi.mock('../../../services/booking', () => ({
  bookingService: {
    getUserBookings: vi.fn().mockRejectedValue(new Error('Mock error')),
    cancelBooking: vi.fn(),
  }
}));

vi.mock('../../../hooks/useWebSocket', () => ({
  default: vi.fn(() => ({
    subscribe: vi.fn(() => vi.fn()),
    isConnected: false,
  }))
}));

vi.mock('../../../hooks/useNotifications', () => ({
  default: vi.fn(() => ({
    notifications: [],
    unreadCount: 0,
    permission: 'default',
    requestPermission: vi.fn(),
    removeNotification: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    clearAll: vi.fn(),
  }))
}));

// Mock Google Maps
global.window.google = {
  maps: {
    Map: vi.fn(),
    Marker: vi.fn(),
    Polyline: vi.fn(),
    MapTypeId: { ROADMAP: 'roadmap' },
    Size: vi.fn(),
    Point: vi.fn(),
  },
};

describe('Tracking Components', () => {
  const mockTripId = 'test-trip-123';

  beforeEach(() => {
    vi.clearAllMocks();
    import.meta.env.VITE_GOOGLE_MAPS_API_KEY = 'test-api-key';
  });

  describe('TripTrackingMap', () => {
    it('renders without crashing', () => {
      render(<TripTrackingMap tripId={mockTripId} />);
      expect(screen.getByText('Loading map...')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<TripTrackingMap tripId={mockTripId} className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('TripStatusDisplay', () => {
    it('renders without crashing', () => {
      render(<TripStatusDisplay tripId={mockTripId} />);
      // Should show loading state initially
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<TripStatusDisplay tripId={mockTripId} className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('ETADisplay', () => {
    it('renders without crashing', () => {
      render(<ETADisplay tripId={mockTripId} />);
      // Should show loading state initially
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<ETADisplay tripId={mockTripId} className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('NotificationCenter', () => {
    it('renders without crashing', () => {
      render(<NotificationCenter tripId={mockTripId} />);
      // Should show notification bell
      expect(document.querySelector('svg')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<NotificationCenter tripId={mockTripId} className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('TripHistory', () => {
    it('renders without crashing', () => {
      render(<TripHistory />);
      // Should show loading state initially
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<TripHistory className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });
});
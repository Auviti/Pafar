/**
 * Test utilities for React component testing
 */
import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a custom render function that includes providers
const AllTheProviders = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (ui, options) =>
  render(ui, { wrapper: AllTheProviders, ...options });

// Mock data factories
export const createMockUser = (overrides = {}) => ({
  id: '1',
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  role: 'passenger',
  isActive: true,
  isVerified: true,
  ...overrides,
});

export const createMockTrip = (overrides = {}) => ({
  id: '1',
  departure_time: '2024-12-25T10:00:00Z',
  arrival_time: '2024-12-25T14:00:00Z',
  fare: 50,
  available_seats: 15,
  estimated_duration: 240,
  origin_terminal: {
    name: 'Central Terminal',
    city: 'New York',
  },
  destination_terminal: {
    name: 'Airport Terminal',
    city: 'Los Angeles',
  },
  bus: {
    model: 'Mercedes Sprinter',
    license_plate: 'ABC-123',
    amenities: ['WiFi', 'AC', 'USB Charging'],
  },
  ...overrides,
});

export const createMockBooking = (overrides = {}) => ({
  id: '1',
  booking_reference: 'BK123456',
  status: 'confirmed',
  payment_status: 'completed',
  seat_numbers: [1, 2],
  total_amount: 100,
  created_at: '2024-12-20T10:00:00Z',
  trip: createMockTrip(),
  ...overrides,
});

export const createMockPayment = (overrides = {}) => ({
  id: '1',
  amount: 100,
  currency: 'USD',
  status: 'completed',
  payment_method: 'card',
  created_at: '2024-12-20T10:00:00Z',
  booking_id: '1',
  ...overrides,
});

// Mock API responses
export const mockApiResponse = (data, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {},
});

export const mockApiError = (message = 'API Error', status = 400) => ({
  response: {
    data: { message },
    status,
    statusText: 'Bad Request',
  },
  message,
});

// Mock localStorage
export const mockLocalStorage = () => {
  const store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
  };
};

// Mock sessionStorage
export const mockSessionStorage = () => {
  const store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
  };
};

// Mock fetch
export const mockFetch = (response) => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(response),
      text: () => Promise.resolve(JSON.stringify(response)),
    })
  );
};

// Mock axios
export const mockAxios = {
  get: vi.fn(() => Promise.resolve({ data: {} })),
  post: vi.fn(() => Promise.resolve({ data: {} })),
  put: vi.fn(() => Promise.resolve({ data: {} })),
  delete: vi.fn(() => Promise.resolve({ data: {} })),
  patch: vi.fn(() => Promise.resolve({ data: {} })),
  create: vi.fn(() => mockAxios),
  defaults: {
    headers: {
      common: {},
    },
  },
  interceptors: {
    request: {
      use: vi.fn(),
      eject: vi.fn(),
    },
    response: {
      use: vi.fn(),
      eject: vi.fn(),
    },
  },
};

// Wait for async operations
export const waitFor = (callback, options = {}) => {
  return new Promise((resolve, reject) => {
    const timeout = options.timeout || 1000;
    const interval = options.interval || 50;
    const startTime = Date.now();

    const check = () => {
      try {
        const result = callback();
        if (result) {
          resolve(result);
        } else if (Date.now() - startTime >= timeout) {
          reject(new Error('Timeout waiting for condition'));
        } else {
          setTimeout(check, interval);
        }
      } catch (error) {
        if (Date.now() - startTime >= timeout) {
          reject(error);
        } else {
          setTimeout(check, interval);
        }
      }
    };

    check();
  });
};

// Re-export everything from testing-library
export * from '@testing-library/react';
export { customRender as render };
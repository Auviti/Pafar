import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with interceptors
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const bookingService = {
  // Search for available trips
  async searchTrips(searchParams) {
    try {
      const response = await apiClient.get('/bookings/search', {
        params: searchParams
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to search trips');
    }
  },

  // Get trip details including seat availability
  async getTripDetails(tripId) {
    try {
      const response = await apiClient.get(`/bookings/trips/${tripId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get trip details');
    }
  },

  // Get available seats for a trip
  async getAvailableSeats(tripId) {
    try {
      const response = await apiClient.get(`/bookings/trips/${tripId}/seats`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get available seats');
    }
  },

  // Reserve seats temporarily
  async reserveSeats(tripId, seatNumbers) {
    try {
      const response = await apiClient.post(`/bookings/trips/${tripId}/reserve`, {
        seat_numbers: seatNumbers
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to reserve seats');
    }
  },

  // Create a booking
  async createBooking(bookingData) {
    try {
      const response = await apiClient.post('/bookings', bookingData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to create booking');
    }
  },

  // Get user's bookings
  async getUserBookings() {
    try {
      const response = await apiClient.get('/bookings/my-bookings');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get bookings');
    }
  },

  // Cancel a booking
  async cancelBooking(bookingId) {
    try {
      const response = await apiClient.post(`/bookings/${bookingId}/cancel`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to cancel booking');
    }
  },

  // Get terminals for route selection
  async getTerminals() {
    try {
      const response = await apiClient.get('/fleet/terminals');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get terminals');
    }
  },

  // Get routes between terminals
  async getRoutes(originId, destinationId) {
    try {
      const response = await apiClient.get('/fleet/routes', {
        params: { origin_id: originId, destination_id: destinationId }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get routes');
    }
  }
};
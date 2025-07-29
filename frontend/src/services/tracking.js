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

export const trackingService = {
  // Get current trip location and status
  async getTripTracking(tripId) {
    try {
      const response = await apiClient.get(`/tracking/trips/${tripId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get trip tracking');
    }
  },

  // Get trip location history
  async getTripLocationHistory(tripId, limit = 50) {
    try {
      const response = await apiClient.get(`/tracking/trips/${tripId}/history`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get location history');
    }
  },

  // Get ETA for a trip
  async getTripETA(tripId) {
    try {
      const response = await apiClient.get(`/tracking/trips/${tripId}/eta`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get ETA');
    }
  },

  // Get trip status updates
  async getTripStatus(tripId) {
    try {
      const response = await apiClient.get(`/tracking/trips/${tripId}/status`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get trip status');
    }
  },

  // Get user's active trips for tracking
  async getActiveTrips() {
    try {
      const response = await apiClient.get('/tracking/active-trips');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get active trips');
    }
  },

  // Get trip route information
  async getTripRoute(tripId) {
    try {
      const response = await apiClient.get(`/tracking/trips/${tripId}/route`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get trip route');
    }
  }
};
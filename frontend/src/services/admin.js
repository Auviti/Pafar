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

export const adminService = {
  // Dashboard metrics
  async getDashboardMetrics() {
    try {
      const response = await apiClient.get('/admin/dashboard/metrics');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch dashboard metrics');
    }
  },

  // User management
  async getUsers(params = {}) {
    try {
      const response = await apiClient.get('/admin/users', { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch users');
    }
  },

  async getUserById(userId) {
    try {
      const response = await apiClient.get(`/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch user');
    }
  },

  async updateUserStatus(userId, status) {
    try {
      const response = await apiClient.patch(`/admin/users/${userId}/status`, { status });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to update user status');
    }
  },

  async suspendUser(userId, reason) {
    try {
      const response = await apiClient.post(`/admin/users/${userId}/suspend`, { reason });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to suspend user');
    }
  },

  // Fleet management
  async getBuses(params = {}) {
    try {
      const response = await apiClient.get('/admin/fleet/buses', { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch buses');
    }
  },

  async createBus(busData) {
    try {
      const response = await apiClient.post('/admin/fleet/buses', busData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to create bus');
    }
  },

  async updateBus(busId, busData) {
    try {
      const response = await apiClient.put(`/admin/fleet/buses/${busId}`, busData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to update bus');
    }
  },

  async getDrivers(params = {}) {
    try {
      const response = await apiClient.get('/admin/fleet/drivers', { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch drivers');
    }
  },

  async assignDriver(tripId, driverId) {
    try {
      const response = await apiClient.post(`/admin/fleet/trips/${tripId}/assign-driver`, {
        driver_id: driverId
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to assign driver');
    }
  },

  // Trip monitoring
  async getTrips(params = {}) {
    try {
      const response = await apiClient.get('/admin/trips', { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch trips');
    }
  },

  async getTripById(tripId) {
    try {
      const response = await apiClient.get(`/admin/trips/${tripId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch trip');
    }
  },

  async updateTripStatus(tripId, status) {
    try {
      const response = await apiClient.patch(`/admin/trips/${tripId}/status`, { status });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to update trip status');
    }
  },

  // Review moderation
  async getReviews(params = {}) {
    try {
      const response = await apiClient.get('/admin/reviews', { params });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch reviews');
    }
  },

  async moderateReview(reviewId, action, reason = '') {
    try {
      const response = await apiClient.post(`/admin/reviews/${reviewId}/moderate`, {
        action,
        reason
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to moderate review');
    }
  },

  async getFlaggedReviews() {
    try {
      const response = await apiClient.get('/admin/reviews/flagged');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch flagged reviews');
    }
  }
};
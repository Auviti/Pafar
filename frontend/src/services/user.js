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

export const userService = {
  // Update user profile
  async updateProfile(profileData) {
    try {
      const response = await apiClient.put('/auth/profile', profileData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to update profile');
    }
  },

  // Get user profile
  async getProfile() {
    try {
      const response = await apiClient.get('/auth/profile');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get profile');
    }
  },

  // Change password
  async changePassword(currentPassword, newPassword) {
    try {
      const response = await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to change password');
    }
  },

  // Get notification preferences
  async getNotificationPreferences() {
    try {
      const response = await apiClient.get('/auth/notification-preferences');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get notification preferences');
    }
  },

  // Update notification preferences
  async updateNotificationPreferences(preferences) {
    try {
      const response = await apiClient.put('/auth/notification-preferences', preferences);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to update notification preferences');
    }
  },

  // Delete user account
  async deleteAccount() {
    try {
      const response = await apiClient.delete('/auth/account');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to delete account');
    }
  }
};
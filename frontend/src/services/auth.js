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

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = Cookies.get('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          Cookies.set('access_token', access_token, { expires: 1 });

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  async login(credentials) {
    try {
      const response = await apiClient.post('/auth/login', credentials);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  },

  async register(userData) {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  async getCurrentUser() {
    try {
      const response = await apiClient.get('/auth/me');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get user');
    }
  },

  async resetPassword(email) {
    try {
      const response = await apiClient.post('/auth/reset-password', { email });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Password reset failed');
    }
  },

  async confirmResetPassword(token, newPassword) {
    try {
      const response = await apiClient.post('/auth/reset-password/confirm', {
        token,
        new_password: newPassword,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Password reset confirmation failed');
    }
  },

  async verifyEmail(token) {
    try {
      const response = await apiClient.post('/auth/verify-email', { token });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Email verification failed');
    }
  },

  async refreshToken(refreshToken) {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Token refresh failed');
    }
  },

  async resendVerification(email) {
    try {
      const response = await apiClient.post('/auth/resend-verification', { email });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to resend verification');
    }
  },
};
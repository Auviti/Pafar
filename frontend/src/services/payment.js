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

export const paymentService = {
  // Create payment intent for booking
  async createPaymentIntent(bookingId, amount) {
    try {
      const response = await apiClient.post('/payments/create-intent', {
        booking_id: bookingId,
        amount: amount
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to create payment intent');
    }
  },

  // Confirm payment
  async confirmPayment(paymentIntentId, paymentMethodId) {
    try {
      const response = await apiClient.post('/payments/confirm', {
        payment_intent_id: paymentIntentId,
        payment_method_id: paymentMethodId
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Payment confirmation failed');
    }
  },

  // Get payment status
  async getPaymentStatus(paymentId) {
    try {
      const response = await apiClient.get(`/payments/${paymentId}/status`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get payment status');
    }
  },

  // Get user's saved payment methods
  async getSavedPaymentMethods() {
    try {
      const response = await apiClient.get('/payments/methods');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get payment methods');
    }
  },

  // Save payment method
  async savePaymentMethod(paymentMethodId) {
    try {
      const response = await apiClient.post('/payments/methods', {
        payment_method_id: paymentMethodId
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to save payment method');
    }
  },

  // Get receipt for payment
  async getReceipt(paymentId) {
    try {
      const response = await apiClient.get(`/payments/${paymentId}/receipt`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get receipt');
    }
  }
};
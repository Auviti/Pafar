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

export const reviewService = {
  // Submit a review for a completed trip
  async submitReview(bookingId, reviewData) {
    try {
      const response = await apiClient.post(`/reviews/bookings/${bookingId}`, reviewData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to submit review');
    }
  },

  // Get user's submitted reviews
  async getUserReviews() {
    try {
      const response = await apiClient.get('/reviews/my-reviews');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get reviews');
    }
  },

  // Get review for a specific booking
  async getBookingReview(bookingId) {
    try {
      const response = await apiClient.get(`/reviews/bookings/${bookingId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get booking review');
    }
  },

  // Update an existing review
  async updateReview(reviewId, reviewData) {
    try {
      const response = await apiClient.put(`/reviews/${reviewId}`, reviewData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to update review');
    }
  },

  // Delete a review
  async deleteReview(reviewId) {
    try {
      const response = await apiClient.delete(`/reviews/${reviewId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to delete review');
    }
  }
};
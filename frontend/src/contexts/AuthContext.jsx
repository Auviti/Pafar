import React, { createContext, useContext, useReducer, useEffect } from 'react';
import Cookies from 'js-cookie';
import { authService } from '../services/auth';

const AuthContext = createContext();

const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

const authReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
        error: null,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = Cookies.get('access_token');
      if (token) {
        try {
          const user = await authService.getCurrentUser();
          dispatch({ type: 'SET_USER', payload: user });
        } catch (error) {
          console.error('Failed to initialize auth:', error);
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
          dispatch({ type: 'SET_ERROR', payload: 'Session expired' });
        }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.login(credentials);
      
      // Store tokens in cookies
      Cookies.set('access_token', response.access_token, { expires: 1 });
      Cookies.set('refresh_token', response.refresh_token, { expires: 7 });
      
      // Get user profile
      const user = await authService.getCurrentUser();
      dispatch({ type: 'SET_USER', payload: user });
      
      return response;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.register(userData);
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const resetPassword = async (email) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.resetPassword(email);
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const confirmResetPassword = async (token, newPassword) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.confirmResetPassword(token, newPassword);
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const verifyEmail = async (token) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.verifyEmail(token);
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const refreshToken = async () => {
    try {
      const refreshToken = Cookies.get('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await authService.refreshToken(refreshToken);
      Cookies.set('access_token', response.access_token, { expires: 1 });
      
      return response.access_token;
    } catch (error) {
      logout();
      throw error;
    }
  };

  const value = {
    ...state,
    login,
    register,
    logout,
    resetPassword,
    confirmResetPassword,
    verifyEmail,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
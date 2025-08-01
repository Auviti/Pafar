/**
 * Global error handling utilities for the frontend application.
 */

class ErrorHandler {
  constructor() {
    this.errorCallbacks = [];
    this.setupGlobalErrorHandlers();
  }

  setupGlobalErrorHandlers() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      this.reportError({
        type: 'unhandledrejection',
        message: event.reason?.message || 'Unhandled promise rejection',
        stack: event.reason?.stack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      });
      
      // Prevent the default browser behavior
      event.preventDefault();
    });

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      console.error('JavaScript error:', event.error);
      this.reportError({
        type: 'javascript',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      });
    });

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        console.error('Resource loading error:', event.target);
        this.reportError({
          type: 'resource',
          message: `Failed to load resource: ${event.target.src || event.target.href}`,
          element: event.target.tagName,
          source: event.target.src || event.target.href,
          timestamp: new Date().toISOString(),
          url: window.location.href
        });
      }
    }, true);

    // Handle network status changes
    window.addEventListener('online', () => {
      this.reportError({
        type: 'network',
        message: 'Network connection restored',
        timestamp: new Date().toISOString(),
        url: window.location.href,
        severity: 'info'
      });
    });

    window.addEventListener('offline', () => {
      this.reportError({
        type: 'network',
        message: 'Network connection lost',
        timestamp: new Date().toISOString(),
        url: window.location.href,
        severity: 'warning'
      });
    });
  }

  addErrorCallback(callback) {
    this.errorCallbacks.push(callback);
  }

  removeErrorCallback(callback) {
    const index = this.errorCallbacks.indexOf(callback);
    if (index > -1) {
      this.errorCallbacks.splice(index, 1);
    }
  }

  async reportError(errorData) {
    // Add additional context
    const enrichedErrorData = {
      ...errorData,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      sessionId: this.getSessionId(),
      userId: this.getUserId(),
      buildVersion: process.env.REACT_APP_VERSION || 'unknown',
      environment: process.env.NODE_ENV,
      memory: performance.memory ? {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
      } : null,
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      } : null,
      localStorage: this.getLocalStorageInfo(),
      cookies: document.cookie ? 'present' : 'none'
    };

    // Call registered callbacks
    this.errorCallbacks.forEach(callback => {
      try {
        callback(enrichedErrorData);
      } catch (callbackError) {
        console.error('Error in error callback:', callbackError);
      }
    });

    // Send to backend with retry logic
    await this.sendErrorToBackend(enrichedErrorData);
  }

  async sendErrorToBackend(errorData, retryCount = 0) {
    const maxRetries = 3;
    const retryDelay = Math.pow(2, retryCount) * 1000; // Exponential backoff

    try {
      const response = await fetch('/api/v1/monitoring/client-errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData),
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Clear any stored errors on successful send
      this.clearStoredErrors();
    } catch (reportingError) {
      console.error('Failed to report error to backend:', reportingError);
      
      // Store error locally for later retry
      this.storeErrorLocally(errorData);
      
      // Retry if we haven't exceeded max retries
      if (retryCount < maxRetries) {
        setTimeout(() => {
          this.sendErrorToBackend(errorData, retryCount + 1);
        }, retryDelay);
      }
    }
  }

  getSessionId() {
    let sessionId = sessionStorage.getItem('pafar_session_id');
    if (!sessionId) {
      sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
      sessionStorage.setItem('pafar_session_id', sessionId);
    }
    return sessionId;
  }

  getUserId() {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      return user.id || null;
    } catch {
      return null;
    }
  }

  getLocalStorageInfo() {
    try {
      const keys = Object.keys(localStorage);
      return {
        keyCount: keys.length,
        totalSize: JSON.stringify(localStorage).length,
        keys: keys.filter(key => !key.includes('sensitive')).slice(0, 10) // Limit and filter sensitive keys
      };
    } catch {
      return { error: 'Unable to access localStorage' };
    }
  }

  storeErrorLocally(errorData) {
    try {
      const storedErrors = JSON.parse(localStorage.getItem('pafar_pending_errors') || '[]');
      storedErrors.push({
        ...errorData,
        storedAt: new Date().toISOString()
      });
      
      // Keep only last 20 errors
      if (storedErrors.length > 20) {
        storedErrors.splice(0, storedErrors.length - 20);
      }
      
      localStorage.setItem('pafar_pending_errors', JSON.stringify(storedErrors));
    } catch (storageError) {
      console.error('Failed to store error locally:', storageError);
    }
  }

  clearStoredErrors() {
    try {
      localStorage.removeItem('pafar_pending_errors');
    } catch (error) {
      console.error('Failed to clear stored errors:', error);
    }
  }

  // Method to retry sending stored errors
  async retrySendingStoredErrors() {
    try {
      const storedErrors = JSON.parse(localStorage.getItem('pafar_pending_errors') || '[]');
      
      for (const errorData of storedErrors) {
        await this.sendErrorToBackend(errorData);
      }
    } catch (error) {
      console.error('Failed to retry sending stored errors:', error);
    }
  }

  handleApiError(error, context = {}) {
    const errorData = {
      type: 'api',
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      context,
      timestamp: new Date().toISOString()
    };

    // Extract error details from response
    if (error.response?.data) {
      errorData.serverError = error.response.data;
      errorData.traceId = error.response.data.trace_id;
    }

    this.reportError(errorData);
    return this.createUserFriendlyError(error);
  }

  createUserFriendlyError(error) {
    const status = error.response?.status;
    const serverMessage = error.response?.data?.error?.message;
    
    let userMessage = 'An unexpected error occurred. Please try again.';
    let severity = 'error';

    switch (status) {
      case 400:
        userMessage = serverMessage || 'Invalid request. Please check your input.';
        severity = 'warning';
        break;
      case 401:
        userMessage = 'You need to log in to access this feature.';
        severity = 'info';
        break;
      case 403:
        userMessage = 'You don\'t have permission to perform this action.';
        severity = 'warning';
        break;
      case 404:
        userMessage = 'The requested resource was not found.';
        severity = 'info';
        break;
      case 409:
        userMessage = serverMessage || 'This action conflicts with the current state.';
        severity = 'warning';
        break;
      case 422:
        userMessage = 'Please check your input and try again.';
        severity = 'warning';
        break;
      case 429:
        userMessage = 'Too many requests. Please wait a moment and try again.';
        severity = 'warning';
        break;
      case 500:
        userMessage = 'Server error. Our team has been notified.';
        severity = 'error';
        break;
      case 502:
      case 503:
      case 504:
        userMessage = 'Service temporarily unavailable. Please try again later.';
        severity = 'warning';
        break;
      default:
        if (serverMessage) {
          userMessage = serverMessage;
        }
    }

    return {
      message: userMessage,
      severity,
      originalError: error,
      traceId: error.response?.data?.trace_id
    };
  }

  handleNetworkError(error) {
    const errorData = {
      type: 'network',
      message: 'Network connection failed',
      originalMessage: error.message,
      timestamp: new Date().toISOString(),
      url: window.location.href
    };

    this.reportError(errorData);

    return {
      message: 'Unable to connect to the server. Please check your internet connection.',
      severity: 'error',
      originalError: error
    };
  }

  handleValidationError(validationErrors) {
    const errorData = {
      type: 'validation',
      message: 'Form validation failed',
      validationErrors,
      timestamp: new Date().toISOString(),
      url: window.location.href
    };

    this.reportError(errorData);

    return {
      message: 'Please correct the highlighted fields and try again.',
      severity: 'warning',
      validationErrors
    };
  }

  // Retry mechanism for failed requests
  async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors (4xx)
        if (error.response?.status >= 400 && error.response?.status < 500) {
          throw error;
        }
        
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay * attempt));
        }
      }
    }
    
    throw lastError;
  }

  // Circuit breaker pattern for repeated failures
  createCircuitBreaker(key, failureThreshold = 5, timeout = 60000) {
    const state = {
      failures: 0,
      lastFailureTime: null,
      state: 'CLOSED' // CLOSED, OPEN, HALF_OPEN
    };

    return async (requestFn) => {
      const now = Date.now();
      
      // Check if circuit should be reset
      if (state.state === 'OPEN' && 
          state.lastFailureTime && 
          now - state.lastFailureTime > timeout) {
        state.state = 'HALF_OPEN';
      }
      
      // Reject if circuit is open
      if (state.state === 'OPEN') {
        throw new Error('Circuit breaker is OPEN');
      }
      
      try {
        const result = await requestFn();
        
        // Reset on success
        state.failures = 0;
        state.state = 'CLOSED';
        
        return result;
      } catch (error) {
        state.failures++;
        state.lastFailureTime = now;
        
        // Open circuit if threshold reached
        if (state.failures >= failureThreshold) {
          state.state = 'OPEN';
        }
        
        throw error;
      }
    };
  }
}

// Create global error handler instance
const errorHandler = new ErrorHandler();

// Export utilities
export default errorHandler;

export const {
  handleApiError,
  handleNetworkError,
  handleValidationError,
  retryRequest,
  createCircuitBreaker,
  addErrorCallback,
  removeErrorCallback
} = errorHandler;
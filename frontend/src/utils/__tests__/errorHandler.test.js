import errorHandler, {
  handleApiError,
  handleNetworkError,
  handleValidationError,
  retryRequest,
  createCircuitBreaker,
} from '../errorHandler';

// Mock fetch for error reporting
global.fetch = jest.fn();

// Mock console methods
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

describe('ErrorHandler', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    console.error = jest.fn();
    console.warn = jest.fn();
    
    // Clear any existing callbacks
    errorHandler.errorCallbacks = [];
  });

  afterEach(() => {
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
  });

  describe('Global Error Handling', () => {
    it('should handle unhandled promise rejections', () => {
      const mockReportError = jest.spyOn(errorHandler, 'reportError').mockImplementation(() => {});
      
      // Simulate unhandled promise rejection
      const event = new Event('unhandledrejection');
      event.reason = new Error('Unhandled promise rejection');
      
      window.dispatchEvent(event);
      
      expect(mockReportError).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'unhandledrejection',
          message: 'Unhandled promise rejection',
        })
      );
      
      mockReportError.mockRestore();
    });

    it('should handle JavaScript errors', () => {
      const mockReportError = jest.spyOn(errorHandler, 'reportError').mockImplementation(() => {});
      
      // Simulate JavaScript error
      const event = new ErrorEvent('error', {
        message: 'JavaScript error',
        filename: 'test.js',
        lineno: 10,
        colno: 5,
        error: new Error('JavaScript error'),
      });
      
      window.dispatchEvent(event);
      
      expect(mockReportError).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'javascript',
          message: 'JavaScript error',
          filename: 'test.js',
          lineno: 10,
          colno: 5,
        })
      );
      
      mockReportError.mockRestore();
    });
  });

  describe('API Error Handling', () => {
    it('should handle 400 Bad Request errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            error: { message: 'Invalid input' },
            trace_id: 'trace-123',
          },
        },
        config: {
          url: '/api/test',
          method: 'POST',
        },
      };

      const result = handleApiError(error);

      expect(result.message).toBe('Invalid input');
      expect(result.severity).toBe('warning');
      expect(result.traceId).toBe('trace-123');
    });

    it('should handle 401 Unauthorized errors', () => {
      const error = {
        response: {
          status: 401,
        },
        config: {
          url: '/api/protected',
          method: 'GET',
        },
      };

      const result = handleApiError(error);

      expect(result.message).toBe('You need to log in to access this feature.');
      expect(result.severity).toBe('info');
    });

    it('should handle 500 Internal Server Error', () => {
      const error = {
        response: {
          status: 500,
          data: {
            error: { message: 'Internal server error' },
          },
        },
        config: {
          url: '/api/test',
          method: 'POST',
        },
      };

      const result = handleApiError(error);

      expect(result.message).toBe('Server error. Our team has been notified.');
      expect(result.severity).toBe('error');
    });

    it('should handle network errors', () => {
      const error = {
        message: 'Network Error',
        code: 'NETWORK_ERROR',
      };

      const result = handleNetworkError(error);

      expect(result.message).toBe('Unable to connect to the server. Please check your internet connection.');
      expect(result.severity).toBe('error');
    });
  });

  describe('Validation Error Handling', () => {
    it('should handle validation errors', () => {
      const validationErrors = {
        email: 'Invalid email format',
        password: 'Password too short',
      };

      const result = handleValidationError(validationErrors);

      expect(result.message).toBe('Please correct the highlighted fields and try again.');
      expect(result.severity).toBe('warning');
      expect(result.validationErrors).toEqual(validationErrors);
    });
  });

  describe('Error Callbacks', () => {
    it('should add and call error callbacks', async () => {
      const callback = jest.fn();
      errorHandler.addErrorCallback(callback);

      await errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      });

      expect(callback).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'test',
          message: 'Test error',
        })
      );
    });

    it('should remove error callbacks', async () => {
      const callback = jest.fn();
      errorHandler.addErrorCallback(callback);
      errorHandler.removeErrorCallback(callback);

      await errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      });

      expect(callback).not.toHaveBeenCalled();
    });

    it('should handle callback errors gracefully', async () => {
      const faultyCallback = jest.fn().mockImplementation(() => {
        throw new Error('Callback error');
      });
      
      errorHandler.addErrorCallback(faultyCallback);

      // Should not throw
      await expect(errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      })).resolves.not.toThrow();

      expect(console.error).toHaveBeenCalledWith(
        'Error in error callback:',
        expect.any(Error)
      );
    });
  });

  describe('Error Reporting', () => {
    it('should report errors to backend with enriched data', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      });

      expect(fetch).toHaveBeenCalledWith('/api/v1/monitoring/client-errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: expect.stringContaining('Test error'),
        signal: expect.any(AbortSignal),
      });

      const callBody = JSON.parse(fetch.mock.calls[0][1].body);
      expect(callBody).toHaveProperty('sessionId');
      expect(callBody).toHaveProperty('buildVersion');
      expect(callBody).toHaveProperty('environment');
    });

    it('should retry failed error reports', async () => {
      fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      await errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      });

      // Should have been called twice (initial + retry)
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should store errors locally when reporting fails', async () => {
      fetch.mockRejectedValue(new Error('Network error'));
      
      const mockSetItem = jest.spyOn(Storage.prototype, 'setItem');
      const mockGetItem = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue('[]');

      await errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      });

      expect(mockSetItem).toHaveBeenCalledWith(
        'pafar_pending_errors',
        expect.stringContaining('Test error')
      );

      mockSetItem.mockRestore();
      mockGetItem.mockRestore();
    });

    it('should handle reporting failures gracefully', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      // Should not throw
      await expect(errorHandler.reportError({
        type: 'test',
        message: 'Test error',
      })).resolves.not.toThrow();

      expect(console.error).toHaveBeenCalledWith(
        'Failed to report error to backend:',
        expect.any(Error)
      );
    });

    it('should retry sending stored errors', async () => {
      const storedErrors = [
        { type: 'test', message: 'Stored error 1', storedAt: new Date().toISOString() },
        { type: 'test', message: 'Stored error 2', storedAt: new Date().toISOString() }
      ];

      jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(JSON.stringify(storedErrors));
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      await errorHandler.retrySendingStoredErrors();

      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Retry Mechanism', () => {
    it('should retry failed requests', async () => {
      let attempts = 0;
      const requestFn = jest.fn().mockImplementation(() => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Temporary error');
        }
        return Promise.resolve('success');
      });

      const result = await retryRequest(requestFn, 3, 10);

      expect(result).toBe('success');
      expect(requestFn).toHaveBeenCalledTimes(3);
    });

    it('should not retry client errors (4xx)', async () => {
      const error = {
        response: { status: 400 },
      };
      
      const requestFn = jest.fn().mockRejectedValue(error);

      await expect(retryRequest(requestFn, 3, 10)).rejects.toEqual(error);
      expect(requestFn).toHaveBeenCalledTimes(1);
    });

    it('should give up after max retries', async () => {
      const error = new Error('Persistent error');
      const requestFn = jest.fn().mockRejectedValue(error);

      await expect(retryRequest(requestFn, 2, 10)).rejects.toEqual(error);
      expect(requestFn).toHaveBeenCalledTimes(3); // Initial + 2 retries
    });
  });

  describe('Circuit Breaker', () => {
    it('should allow requests when circuit is closed', async () => {
      const circuitBreaker = createCircuitBreaker('test', 3, 1000);
      const requestFn = jest.fn().mockResolvedValue('success');

      const result = await circuitBreaker(requestFn);

      expect(result).toBe('success');
      expect(requestFn).toHaveBeenCalledTimes(1);
    });

    it('should open circuit after threshold failures', async () => {
      const circuitBreaker = createCircuitBreaker('test', 2, 1000);
      const requestFn = jest.fn().mockRejectedValue(new Error('Service error'));

      // Trigger failures to open circuit
      for (let i = 0; i < 3; i++) {
        try {
          await circuitBreaker(requestFn);
        } catch (error) {
          // Expected
        }
      }

      // Next request should be rejected immediately
      await expect(circuitBreaker(requestFn)).rejects.toThrow('Circuit breaker is OPEN');
    });

    it('should reset circuit after timeout', async () => {
      jest.useFakeTimers();
      
      const circuitBreaker = createCircuitBreaker('test', 1, 100);
      const requestFn = jest.fn()
        .mockRejectedValueOnce(new Error('Service error'))
        .mockResolvedValueOnce('success');

      // Trigger failure to open circuit
      try {
        await circuitBreaker(requestFn);
      } catch (error) {
        // Expected
      }

      // Fast-forward time to reset circuit
      jest.advanceTimersByTime(150);

      // Should allow request again
      const result = await circuitBreaker(requestFn);
      expect(result).toBe('success');

      jest.useRealTimers();
    });
  });
});
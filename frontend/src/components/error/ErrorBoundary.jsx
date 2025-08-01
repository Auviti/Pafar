import React from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    });

    // Send error to monitoring service
    this.reportError(error, errorInfo);
  }

  reportError = async (error, errorInfo) => {
    try {
      const errorReport = {
        type: 'react_error_boundary',
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo?.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        errorId: this.state.errorId,
        retryCount: this.state.retryCount,
        props: this.props.errorContext || {},
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        },
        memory: performance.memory ? {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize
        } : null,
        connection: navigator.connection ? {
          effectiveType: navigator.connection.effectiveType,
          downlink: navigator.connection.downlink
        } : null
      };

      // Send to backend monitoring endpoint with retry logic
      await this.sendErrorReport(errorReport);
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
      // Store error locally for later retry
      this.storeErrorLocally(error, errorInfo);
    }
  };

  sendErrorReport = async (errorReport, retryCount = 0) => {
    const maxRetries = 3;
    const retryDelay = Math.pow(2, retryCount) * 1000; // Exponential backoff

    try {
      const response = await fetch('/api/v1/monitoring/client-errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport),
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      if (retryCount < maxRetries) {
        setTimeout(() => {
          this.sendErrorReport(errorReport, retryCount + 1);
        }, retryDelay);
      } else {
        throw error;
      }
    }
  };

  storeErrorLocally = (error, errorInfo) => {
    try {
      const errorData = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo?.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        errorId: this.state.errorId
      };

      const storedErrors = JSON.parse(localStorage.getItem('pafar_errors') || '[]');
      storedErrors.push(errorData);
      
      // Keep only last 10 errors
      if (storedErrors.length > 10) {
        storedErrors.splice(0, storedErrors.length - 10);
      }
      
      localStorage.setItem('pafar_errors', JSON.stringify(storedErrors));
    } catch (storageError) {
      console.error('Failed to store error locally:', storageError);
    }
  };

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback(
          this.state.error,
          this.state.errorInfo,
          this.handleRetry
        );
      }

      // Default fallback UI
      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            
            <h2>Oops! Something went wrong</h2>
            <p>We're sorry, but something unexpected happened. Our team has been notified.</p>
            
            {this.props.showDetails && this.state.error && (
              <details className="error-details">
                <summary>Error Details</summary>
                <div className="error-info">
                  <p><strong>Error ID:</strong> {this.state.errorId}</p>
                  <p><strong>Message:</strong> {this.state.error.message}</p>
                  <p><strong>Retry Count:</strong> {this.state.retryCount}</p>
                  <p><strong>Timestamp:</strong> {new Date().toLocaleString()}</p>
                  <p><strong>URL:</strong> {window.location.href}</p>
                  {this.state.error.stack && (
                    <details className="error-stack-details">
                      <summary>Stack Trace</summary>
                      <pre className="error-stack">{this.state.error.stack}</pre>
                    </details>
                  )}
                  {this.state.errorInfo?.componentStack && (
                    <details className="component-stack-details">
                      <summary>Component Stack</summary>
                      <pre className="component-stack">{this.state.errorInfo.componentStack}</pre>
                    </details>
                  )}
                </div>
              </details>
            )}
            
            <div className="error-actions">
              <button 
                onClick={this.handleRetry}
                className="btn btn-primary"
                disabled={this.state.retryCount >= 3}
              >
                {this.state.retryCount >= 3 ? 'Max Retries Reached' : 'Try Again'}
              </button>
              <button 
                onClick={this.handleReload}
                className="btn btn-secondary"
              >
                Reload Page
              </button>
              <button 
                onClick={() => this.reportError(this.state.error, this.state.errorInfo)}
                className="btn btn-outline"
              >
                Send Report
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.func,
  showDetails: PropTypes.bool,
  errorContext: PropTypes.object,
  onError: PropTypes.func
};

ErrorBoundary.defaultProps = {
  showDetails: process.env.NODE_ENV === 'development',
  errorContext: {},
  onError: null
};

export default ErrorBoundary;
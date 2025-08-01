import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const ErrorFallback = ({ 
  error, 
  errorInfo, 
  resetError, 
  errorId,
  retryCount = 0 
}) => {
  const [isReporting, setIsReporting] = useState(false);
  const [reportSent, setReportSent] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Auto-report critical errors
    if (error && !reportSent && retryCount === 0) {
      handleSendReport();
    }
  }, [error, reportSent, retryCount]);

  const handleSendReport = async () => {
    if (isReporting || reportSent) return;

    setIsReporting(true);
    try {
      const errorReport = {
        type: 'react_error_boundary',
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo?.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        errorId: errorId,
        retryCount: retryCount,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      };

      await fetch('/api/v1/monitoring/client-errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport)
      });

      setReportSent(true);
    } catch (reportingError) {
      console.error('Failed to send error report:', reportingError);
    } finally {
      setIsReporting(false);
    }
  };

  const handleReload = () => {
    window.location.reload();
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  const copyErrorId = () => {
    if (errorId) {
      navigator.clipboard.writeText(errorId).then(() => {
        // Could show a toast notification here
        console.log('Error ID copied to clipboard');
      });
    }
  };

  const getErrorSeverity = () => {
    if (error.name === 'ChunkLoadError') return 'warning';
    if (error.message?.includes('Network')) return 'warning';
    return 'error';
  };

  const getErrorIcon = () => {
    const severity = getErrorSeverity();
    switch (severity) {
      case 'warning':
        return '⚠️';
      case 'error':
      default:
        return '❌';
    }
  };

  const getErrorTitle = () => {
    const severity = getErrorSeverity();
    switch (severity) {
      case 'warning':
        return 'Something went wrong';
      case 'error':
      default:
        return 'Oops! An error occurred';
    }
  };

  const getErrorMessage = () => {
    if (error.name === 'ChunkLoadError') {
      return 'Failed to load application resources. This might be due to a network issue or an app update.';
    }
    if (error.message?.includes('Network')) {
      return 'Network connection issue detected. Please check your internet connection.';
    }
    return 'We encountered an unexpected error. Our team has been notified and is working on a fix.';
  };

  const getSuggestions = () => {
    if (error.name === 'ChunkLoadError') {
      return [
        'Try refreshing the page',
        'Check your internet connection',
        'Clear your browser cache'
      ];
    }
    if (error.message?.includes('Network')) {
      return [
        'Check your internet connection',
        'Try again in a few moments',
        'Contact support if the issue persists'
      ];
    }
    return [
      'Try refreshing the page',
      'Go back to the home page',
      'Contact support if the issue continues'
    ];
  };

  return (
    <div className="error-fallback">
      <div className="error-fallback-container">
        <div className="error-icon">
          <span role="img" aria-label="Error" style={{ fontSize: '4rem' }}>
            {getErrorIcon()}
          </span>
        </div>

        <h1 className="error-title">{getErrorTitle()}</h1>
        
        <p className="error-message">{getErrorMessage()}</p>

        {errorId && (
          <div className="error-id-section">
            <p className="error-id">
              <strong>Error ID:</strong> 
              <code onClick={copyErrorId} style={{ cursor: 'pointer', marginLeft: '8px' }}>
                {errorId}
              </code>
              <button 
                onClick={copyErrorId}
                className="copy-button"
                title="Copy Error ID"
              >
                📋
              </button>
            </p>
            {reportSent && (
              <p className="report-status success">
                ✅ Error report sent successfully
              </p>
            )}
          </div>
        )}

        <div className="suggestions">
          <h3>What you can try:</h3>
          <ul>
            {getSuggestions().map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>

        <div className="error-actions">
          <button 
            onClick={resetError}
            className="btn btn-primary"
            disabled={retryCount >= 3}
          >
            {retryCount >= 3 ? 'Max Retries Reached' : 'Try Again'}
          </button>
          
          <button 
            onClick={handleReload}
            className="btn btn-secondary"
          >
            Refresh Page
          </button>
          
          <button 
            onClick={handleGoHome}
            className="btn btn-outline"
          >
            Go Home
          </button>

          {!reportSent && (
            <button 
              onClick={handleSendReport}
              className="btn btn-outline"
              disabled={isReporting}
            >
              {isReporting ? 'Sending...' : 'Send Report'}
            </button>
          )}
        </div>

        {process.env.NODE_ENV === 'development' && (
          <div className="error-details-section">
            <button 
              onClick={() => setShowDetails(!showDetails)}
              className="btn btn-text"
            >
              {showDetails ? 'Hide' : 'Show'} Technical Details
            </button>
            
            {showDetails && (
              <div className="error-details">
                <div className="error-detail-item">
                  <strong>Error:</strong>
                  <pre>{error.message}</pre>
                </div>
                
                {error.stack && (
                  <div className="error-detail-item">
                    <strong>Stack Trace:</strong>
                    <pre className="stack-trace">{error.stack}</pre>
                  </div>
                )}
                
                {errorInfo?.componentStack && (
                  <div className="error-detail-item">
                    <strong>Component Stack:</strong>
                    <pre className="component-stack">{errorInfo.componentStack}</pre>
                  </div>
                )}
                
                <div className="error-detail-item">
                  <strong>URL:</strong>
                  <code>{window.location.href}</code>
                </div>
                
                <div className="error-detail-item">
                  <strong>Timestamp:</strong>
                  <code>{new Date().toLocaleString()}</code>
                </div>
                
                <div className="error-detail-item">
                  <strong>User Agent:</strong>
                  <code>{navigator.userAgent}</code>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .error-fallback {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .error-fallback-container {
          max-width: 600px;
          background: white;
          border-radius: 12px;
          padding: 3rem;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
          text-align: center;
        }

        .error-icon {
          margin-bottom: 1.5rem;
        }

        .error-title {
          color: #2d3748;
          font-size: 2rem;
          font-weight: 600;
          margin-bottom: 1rem;
        }

        .error-message {
          color: #4a5568;
          font-size: 1.1rem;
          line-height: 1.6;
          margin-bottom: 2rem;
        }

        .error-id-section {
          background: #f7fafc;
          border-radius: 8px;
          padding: 1rem;
          margin-bottom: 2rem;
        }

        .error-id {
          margin: 0;
          font-size: 0.9rem;
          color: #4a5568;
        }

        .error-id code {
          background: #e2e8f0;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-family: 'Monaco', 'Menlo', monospace;
        }

        .copy-button {
          background: none;
          border: none;
          cursor: pointer;
          margin-left: 0.5rem;
          padding: 0.25rem;
          border-radius: 4px;
        }

        .copy-button:hover {
          background: #e2e8f0;
        }

        .report-status.success {
          color: #38a169;
          font-size: 0.9rem;
          margin-top: 0.5rem;
          margin-bottom: 0;
        }

        .suggestions {
          text-align: left;
          margin-bottom: 2rem;
        }

        .suggestions h3 {
          color: #2d3748;
          font-size: 1.1rem;
          margin-bottom: 0.5rem;
        }

        .suggestions ul {
          color: #4a5568;
          padding-left: 1.5rem;
        }

        .suggestions li {
          margin-bottom: 0.25rem;
        }

        .error-actions {
          display: flex;
          gap: 1rem;
          justify-content: center;
          flex-wrap: wrap;
          margin-bottom: 2rem;
        }

        .btn {
          padding: 0.75rem 1.5rem;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
          font-size: 0.9rem;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background: #4299e1;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #3182ce;
        }

        .btn-secondary {
          background: #718096;
          color: white;
        }

        .btn-secondary:hover {
          background: #4a5568;
        }

        .btn-outline {
          background: transparent;
          color: #4299e1;
          border: 1px solid #4299e1;
        }

        .btn-outline:hover {
          background: #4299e1;
          color: white;
        }

        .btn-text {
          background: none;
          color: #4299e1;
          text-decoration: underline;
        }

        .error-details-section {
          border-top: 1px solid #e2e8f0;
          padding-top: 2rem;
          text-align: left;
        }

        .error-details {
          margin-top: 1rem;
        }

        .error-detail-item {
          margin-bottom: 1rem;
        }

        .error-detail-item strong {
          display: block;
          color: #2d3748;
          margin-bottom: 0.25rem;
        }

        .error-detail-item pre {
          background: #f7fafc;
          padding: 0.75rem;
          border-radius: 4px;
          overflow-x: auto;
          font-size: 0.8rem;
          color: #4a5568;
        }

        .error-detail-item code {
          background: #f7fafc;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.8rem;
          color: #4a5568;
        }

        .stack-trace, .component-stack {
          max-height: 200px;
          overflow-y: auto;
        }
      `}</style>
    </div>
  );
};

ErrorFallback.propTypes = {
  error: PropTypes.object.isRequired,
  errorInfo: PropTypes.object,
  resetError: PropTypes.func.isRequired,
  errorId: PropTypes.string,
  retryCount: PropTypes.number
};

export default ErrorFallback;
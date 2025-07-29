import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const ProtectedRoute = ({ children, requiredRole = null, fallback = null }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      fallback || (
        <div className="loading-container">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        </div>
      )
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access if required
  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="access-denied-container">
        <div className="access-denied">
          <h2>Access Denied</h2>
          <p>You don't have permission to access this page.</p>
          <button onClick={() => window.history.back()}>Go Back</button>
        </div>
      </div>
    );
  }

  return children;
};

// Higher-order component for protecting routes
export const withAuth = (Component, requiredRole = null) => {
  return function AuthenticatedComponent(props) {
    return (
      <ProtectedRoute requiredRole={requiredRole}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };
};

// Component for redirecting authenticated users away from auth pages
export const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect authenticated users to dashboard
  if (isAuthenticated) {
    const from = location.state?.from?.pathname || '/dashboard';
    return <Navigate to={from} replace />;
  }

  return children;
};

export default ProtectedRoute;
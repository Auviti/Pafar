import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import ErrorBoundary from './components/error/ErrorBoundary';
import ErrorFallback from './components/error/ErrorFallback';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import ForgotPasswordForm from './components/auth/ForgotPasswordForm';
import ResetPasswordForm from './components/auth/ResetPasswordForm';
import EmailVerification from './components/auth/EmailVerification';
import ProtectedRoute, { PublicRoute } from './components/auth/ProtectedRoute';
import BookingPage from './pages/BookingPage';
import AdminLayout from './components/admin/AdminLayout';
import AdminDashboard from './components/admin/AdminDashboard';
import UserManagement from './components/admin/UserManagement';
import FleetManagement from './components/admin/FleetManagement';
import TripMonitoring from './components/admin/TripMonitoring';
import ReviewModeration from './components/admin/ReviewModeration';
import './assets/css/auth.css';
import './assets/css/booking.css';
import './assets/css/admin.css';
import './assets/css/error.css';
import './App.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Placeholder Dashboard component
const Dashboard = () => (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h1>Dashboard</h1>
    <p>Welcome to your dashboard!</p>
    <p>This is a protected route that requires authentication.</p>
  </div>
);

function App() {
  return (
    <ErrorBoundary fallback={(error, errorInfo, retry) => (
      <ErrorFallback 
        error={error} 
        errorInfo={errorInfo} 
        retry={retry}
        errorId={Date.now().toString(36) + Math.random().toString(36).substr(2)}
      />
    )}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AuthProvider>
            <div className="App">
            <Routes>
              {/* Public routes - redirect to dashboard if authenticated */}
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <LoginForm />
                  </PublicRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <PublicRoute>
                    <RegisterForm />
                  </PublicRoute>
                }
              />
              <Route
                path="/forgot-password"
                element={
                  <PublicRoute>
                    <ForgotPasswordForm />
                  </PublicRoute>
                }
              />
              <Route
                path="/reset-password"
                element={
                  <PublicRoute>
                    <ResetPasswordForm />
                  </PublicRoute>
                }
              />
              <Route path="/verify-email" element={<EmailVerification />} />

              {/* Protected routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/booking"
                element={
                  <ProtectedRoute>
                    <BookingPage />
                  </ProtectedRoute>
                }
              />

              {/* Admin routes - require admin role */}
              <Route
                path="/admin/*"
                element={
                  <ProtectedRoute requiredRole="admin">
                    <AdminLayout>
                      <Routes>
                        <Route path="dashboard" element={<AdminDashboard />} />
                        <Route path="users" element={<UserManagement />} />
                        <Route path="fleet" element={<FleetManagement />} />
                        <Route path="trips" element={<TripMonitoring />} />
                        <Route path="reviews" element={<ReviewModeration />} />
                        <Route path="" element={<Navigate to="dashboard" replace />} />
                      </Routes>
                    </AdminLayout>
                  </ProtectedRoute>
                }
              />

              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />

              {/* Catch all route */}
              <Route
                path="*"
                element={
                  <div style={{ padding: '20px', textAlign: 'center' }}>
                    <h1>404 - Page Not Found</h1>
                    <p>The page you're looking for doesn't exist.</p>
                  </div>
                }
              />
            </Routes>
          </div>
        </AuthProvider>
      </Router>
    </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;

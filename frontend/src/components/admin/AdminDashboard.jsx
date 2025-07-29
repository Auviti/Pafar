import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminService } from '../../services/admin';

const AdminDashboard = () => {
  const [timeRange, setTimeRange] = useState('7d');

  const { data: metrics, isLoading, error, refetch } = useQuery({
    queryKey: ['admin-metrics', timeRange],
    queryFn: () => adminService.getDashboardMetrics({ timeRange }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const MetricCard = ({ title, value, change, icon, color = 'blue' }) => (
    <div className={`metric-card metric-${color}`}>
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      <div className="metric-value">{value}</div>
      {change && (
        <div className={`metric-change ${change >= 0 ? 'positive' : 'negative'}`}>
          {change >= 0 ? '↗' : '↘'} {Math.abs(change)}%
        </div>
      )}
    </div>
  );

  const LiveTripCard = ({ trip }) => (
    <div className="live-trip-card">
      <div className="trip-info">
        <h4>{trip.route}</h4>
        <p>Bus: {trip.bus_number}</p>
        <p>Driver: {trip.driver_name}</p>
      </div>
      <div className="trip-status">
        <span className={`status-badge status-${trip.status}`}>
          {trip.status}
        </span>
        <p>{trip.passengers}/{trip.capacity} passengers</p>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner" data-testid="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h3>Error loading dashboard</h3>
        <p>{error.message}</p>
        <button onClick={() => refetch()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h2>Dashboard Overview</h2>
        <div className="time-range-selector">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <MetricCard
          title="Total Bookings"
          value={metrics?.total_bookings || 0}
          change={metrics?.bookings_change}
          icon="🎫"
          color="blue"
        />
        <MetricCard
          title="Active Users"
          value={metrics?.active_users || 0}
          change={metrics?.users_change}
          icon="👥"
          color="green"
        />
        <MetricCard
          title="Revenue"
          value={`$${metrics?.revenue || 0}`}
          change={metrics?.revenue_change}
          icon="💰"
          color="purple"
        />
        <MetricCard
          title="Fleet Utilization"
          value={`${metrics?.fleet_utilization || 0}%`}
          change={metrics?.utilization_change}
          icon="🚌"
          color="orange"
        />
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        <div className="chart-container">
          <h3>Booking Trends</h3>
          <div className="chart-placeholder">
            <p>Chart visualization would go here</p>
            <p>Bookings over time: {metrics?.booking_trend?.join(', ')}</p>
          </div>
        </div>
        <div className="chart-container">
          <h3>Revenue Analysis</h3>
          <div className="chart-placeholder">
            <p>Revenue chart would go here</p>
            <p>Daily revenue: ${metrics?.daily_revenue || 0}</p>
          </div>
        </div>
      </div>

      {/* Live Data Section */}
      <div className="live-section">
        <div className="live-trips">
          <h3>Live Trips ({metrics?.live_trips?.length || 0})</h3>
          <div className="live-trips-grid">
            {metrics?.live_trips?.length > 0 ? (
              metrics.live_trips.map((trip) => (
                <LiveTripCard key={trip.id} trip={trip} />
              ))
            ) : (
              <p>No active trips</p>
            )}
          </div>
        </div>

        <div className="recent-activity">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            {metrics?.recent_activities?.length > 0 ? (
              metrics.recent_activities.map((activity, index) => (
                <div key={index} className="activity-item">
                  <span className="activity-time">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="activity-text">{activity.message}</span>
                </div>
              ))
            ) : (
              <p>No recent activity</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button className="action-btn primary">
            📊 Generate Report
          </button>
          <button className="action-btn secondary">
            🚨 View Alerts
          </button>
          <button className="action-btn secondary">
            📧 Send Notifications
          </button>
          <button className="action-btn secondary">
            ⚙️ System Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
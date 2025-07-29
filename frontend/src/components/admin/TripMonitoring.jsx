import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../services/admin';

const TripMonitoring = () => {
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterDate, setFilterDate] = useState('today');
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [showTripModal, setShowTripModal] = useState(false);

  const queryClient = useQueryClient();

  const { data: tripsData, isLoading, error } = useQuery({
    queryKey: ['admin-trips', filterStatus, filterDate],
    queryFn: () => adminService.getTrips({
      status: filterStatus !== 'all' ? filterStatus : undefined,
      date: filterDate
    }),
    refetchInterval: 30000, // Refresh every 30 seconds for real-time updates
  });

  const updateTripStatusMutation = useMutation({
    mutationFn: ({ tripId, status }) => adminService.updateTripStatus(tripId, status),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-trips']);
      setShowTripModal(false);
    },
  });

  const handleStatusUpdate = (tripId, newStatus) => {
    if (window.confirm(`Are you sure you want to change trip status to ${newStatus}?`)) {
      updateTripStatusMutation.mutate({ tripId, status: newStatus });
    }
  };

  const TripModal = ({ trip, onClose }) => (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Trip Details - {trip.route}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="trip-details-grid">
            <div className="trip-info">
              <h4>Trip Information</h4>
              <div className="detail-row">
                <label>Route:</label>
                <span>{trip.route}</span>
              </div>
              <div className="detail-row">
                <label>Bus:</label>
                <span>{trip.bus_number} ({trip.bus_model})</span>
              </div>
              <div className="detail-row">
                <label>Driver:</label>
                <span>{trip.driver_name}</span>
              </div>
              <div className="detail-row">
                <label>Status:</label>
                <span className={`status-badge status-${trip.status}`}>
                  {trip.status}
                </span>
              </div>
              <div className="detail-row">
                <label>Departure:</label>
                <span>{new Date(trip.departure_time).toLocaleString()}</span>
              </div>
              <div className="detail-row">
                <label>Estimated Arrival:</label>
                <span>{trip.estimated_arrival ? new Date(trip.estimated_arrival).toLocaleString() : 'N/A'}</span>
              </div>
            </div>

            <div className="passenger-info">
              <h4>Passenger Information</h4>
              <div className="passenger-stats">
                <div className="stat">
                  <span className="stat-value">{trip.booked_seats}</span>
                  <span className="stat-label">Booked Seats</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{trip.capacity - trip.booked_seats}</span>
                  <span className="stat-label">Available Seats</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{Math.round((trip.booked_seats / trip.capacity) * 100)}%</span>
                  <span className="stat-label">Occupancy</span>
                </div>
              </div>
            </div>

            <div className="location-info">
              <h4>Current Location</h4>
              {trip.current_location ? (
                <div>
                  <p><strong>Coordinates:</strong> {trip.current_location.lat}, {trip.current_location.lng}</p>
                  <p><strong>Last Update:</strong> {new Date(trip.current_location.timestamp).toLocaleString()}</p>
                  <p><strong>Speed:</strong> {trip.current_location.speed || 0} km/h</p>
                </div>
              ) : (
                <p>Location not available</p>
              )}
            </div>

            <div className="revenue-info">
              <h4>Revenue Information</h4>
              <div className="detail-row">
                <label>Fare per Seat:</label>
                <span>${trip.fare}</span>
              </div>
              <div className="detail-row">
                <label>Total Revenue:</label>
                <span>${trip.total_revenue}</span>
              </div>
              <div className="detail-row">
                <label>Payment Status:</label>
                <span>{trip.payments_completed}/{trip.booked_seats} completed</span>
              </div>
            </div>
          </div>

          <div className="trip-actions">
            <h4>Trip Actions</h4>
            <div className="action-buttons">
              <button 
                className="btn btn-success"
                onClick={() => handleStatusUpdate(trip.id, 'in_progress')}
                disabled={trip.status === 'in_progress'}
              >
                Start Trip
              </button>
              <button 
                className="btn btn-warning"
                onClick={() => handleStatusUpdate(trip.id, 'delayed')}
                disabled={trip.status === 'delayed'}
              >
                Mark Delayed
              </button>
              <button 
                className="btn btn-info"
                onClick={() => handleStatusUpdate(trip.id, 'completed')}
                disabled={trip.status === 'completed'}
              >
                Complete Trip
              </button>
              <button 
                className="btn btn-danger"
                onClick={() => handleStatusUpdate(trip.id, 'cancelled')}
                disabled={trip.status === 'cancelled'}
              >
                Cancel Trip
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const TripCard = ({ trip }) => (
    <div className="trip-card">
      <div className="trip-header">
        <div className="trip-route">
          <h4>{trip.route}</h4>
          <p>{trip.origin} → {trip.destination}</p>
        </div>
        <span className={`status-badge status-${trip.status}`}>
          {trip.status}
        </span>
      </div>
      
      <div className="trip-details">
        <div className="detail-item">
          <span className="label">Bus:</span>
          <span>{trip.bus_number}</span>
        </div>
        <div className="detail-item">
          <span className="label">Driver:</span>
          <span>{trip.driver_name}</span>
        </div>
        <div className="detail-item">
          <span className="label">Departure:</span>
          <span>{new Date(trip.departure_time).toLocaleTimeString()}</span>
        </div>
        <div className="detail-item">
          <span className="label">Passengers:</span>
          <span>{trip.booked_seats}/{trip.capacity}</span>
        </div>
      </div>

      <div className="trip-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${(trip.booked_seats / trip.capacity) * 100}%` }}
          ></div>
        </div>
        <span className="progress-text">
          {Math.round((trip.booked_seats / trip.capacity) * 100)}% full
        </span>
      </div>

      <div className="trip-actions">
        <button 
          className="btn btn-sm btn-info"
          onClick={() => {
            setSelectedTrip(trip);
            setShowTripModal(true);
          }}
        >
          View Details
        </button>
        <button className="btn btn-sm btn-primary">
          Track Live
        </button>
        {trip.status === 'scheduled' && (
          <button 
            className="btn btn-sm btn-success"
            onClick={() => handleStatusUpdate(trip.id, 'in_progress')}
          >
            Start Trip
          </button>
        )}
      </div>
    </div>
  );

  if (isLoading) {
    return <div className="loading">Loading trips...</div>;
  }

  if (error) {
    return <div className="error">Error loading trips: {error.message}</div>;
  }

  return (
    <div className="trip-monitoring">
      <div className="page-header">
        <h2>Trip Monitoring</h2>
        <div className="header-stats">
          <div className="stat-item">
            <span className="stat-value">{tripsData?.stats?.active || 0}</span>
            <span className="stat-label">Active Trips</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{tripsData?.stats?.scheduled || 0}</span>
            <span className="stat-label">Scheduled</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{tripsData?.stats?.completed || 0}</span>
            <span className="stat-label">Completed Today</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="filter-group">
          <label>Status:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">All Status</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="delayed">Delayed</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Date:</label>
          <select value={filterDate} onChange={(e) => setFilterDate(e.target.value)}>
            <option value="today">Today</option>
            <option value="tomorrow">Tomorrow</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
        <button className="btn btn-secondary">
          🔄 Refresh
        </button>
      </div>

      {/* Trips Grid */}
      <div className="trips-grid">
        {tripsData?.trips?.length > 0 ? (
          tripsData.trips.map(trip => (
            <TripCard key={trip.id} trip={trip} />
          ))
        ) : (
          <p>No trips found</p>
        )}
      </div>

      {/* Trip Details Modal */}
      {showTripModal && selectedTrip && (
        <TripModal 
          trip={selectedTrip} 
          onClose={() => setShowTripModal(false)} 
        />
      )}
    </div>
  );
};

export default TripMonitoring;
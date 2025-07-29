import React, { useState, useEffect } from 'react';
import { bookingService } from '../../services/booking';

const TripHistory = ({ className = '' }) => {
  const [bookings, setBookings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, completed, cancelled, upcoming
  const [sortBy, setSortBy] = useState('date_desc'); // date_desc, date_asc

  // Load user bookings
  useEffect(() => {
    const loadBookings = async () => {
      try {
        setIsLoading(true);
        const data = await bookingService.getUserBookings();
        setBookings(data.bookings || []);
        setError(null);
      } catch (err) {
        console.error('Failed to load bookings:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    loadBookings();
  }, []);

  // Filter and sort bookings
  const filteredAndSortedBookings = bookings
    .filter(booking => {
      switch (filter) {
        case 'completed':
          return booking.status === 'completed';
        case 'cancelled':
          return booking.status === 'cancelled';
        case 'upcoming':
          return ['confirmed', 'in_progress'].includes(booking.status) && 
                 new Date(booking.trip.departure_time) > new Date();
        default:
          return true;
      }
    })
    .sort((a, b) => {
      const dateA = new Date(a.trip.departure_time);
      const dateB = new Date(b.trip.departure_time);
      
      switch (sortBy) {
        case 'date_asc':
          return dateA - dateB;
        default:
          return dateB - dateA;
      }
    });

  // Get status badge
  const getStatusBadge = (status) => {
    const statusConfig = {
      confirmed: { color: 'bg-blue-100 text-blue-800', label: 'Confirmed' },
      in_progress: { color: 'bg-green-100 text-green-800', label: 'In Progress' },
      completed: { color: 'bg-gray-100 text-gray-800', label: 'Completed' },
      cancelled: { color: 'bg-red-100 text-red-800', label: 'Cancelled' },
      pending: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((date - now) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays === -1) return 'Yesterday';
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  // Format time
  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Handle booking action (cancel, view details, etc.)
  const handleBookingAction = async (bookingId, action) => {
    try {
      if (action === 'cancel') {
        await bookingService.cancelBooking(bookingId);
        // Refresh bookings
        const data = await bookingService.getUserBookings();
        setBookings(data.bookings || []);
      }
    } catch (err) {
      console.error(`Failed to ${action} booking:`, err);
      // Handle error (show toast, etc.)
    }
  };

  if (isLoading) {
    return (
      <div className={`${className}`}>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-gray-200 h-24 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <div className="text-red-600 mr-2">⚠️</div>
          <div>
            <p className="text-red-800 font-medium">Failed to load trip history</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Trip History</h2>
        
        {/* Controls */}
        <div className="flex space-x-3">
          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Trips</option>
            <option value="upcoming">Upcoming</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          
          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="date_desc">Newest First</option>
            <option value="date_asc">Oldest First</option>
          </select>
        </div>
      </div>

      {/* Bookings List */}
      {filteredAndSortedBookings.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No trips found</h3>
          <p className="text-gray-600">
            {filter === 'all' ? 
              "You haven't booked any trips yet." :
              `No ${filter} trips found.`
            }
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAndSortedBookings.map(booking => (
            <div key={booking.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="text-sm font-medium text-gray-900">
                    {booking.booking_reference}
                  </div>
                  {getStatusBadge(booking.status)}
                </div>
                
                <div className="text-sm text-gray-500">
                  {formatDate(booking.trip.departure_time)}
                </div>
              </div>

              {/* Route Info */}
              <div className="flex items-center mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <div className="text-sm font-medium text-gray-900">
                      {booking.trip.origin_terminal}
                    </div>
                    <div className="text-gray-400">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </div>
                    <div className="text-sm font-medium text-gray-900">
                      {booking.trip.destination_terminal}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatTime(booking.trip.departure_time)} - {formatTime(booking.trip.arrival_time)}
                  </div>
                </div>
              </div>

              {/* Trip Details */}
              <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                <div>
                  <span className="text-gray-500">Seats:</span>
                  <div className="font-medium">
                    {booking.seat_numbers.join(', ')}
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-500">Amount:</span>
                  <div className="font-medium">
                    ${booking.total_amount}
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-500">Bus:</span>
                  <div className="font-medium">
                    {booking.trip.bus_license_plate || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="flex space-x-2">
                  {/* Track button for active trips */}
                  {['confirmed', 'in_progress'].includes(booking.status) && 
                   new Date(booking.trip.departure_time) > new Date() && (
                    <button
                      onClick={() => window.location.href = `/tracking/${booking.trip.id}`}
                      className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                    >
                      Track Trip
                    </button>
                  )}
                  
                  {/* Cancel button for confirmed trips */}
                  {booking.status === 'confirmed' && 
                   new Date(booking.trip.departure_time) > new Date() && (
                    <button
                      onClick={() => handleBookingAction(booking.id, 'cancel')}
                      className="text-sm border border-red-300 text-red-600 px-3 py-1 rounded hover:bg-red-50"
                    >
                      Cancel
                    </button>
                  )}
                  
                  {/* Rate trip button for completed trips */}
                  {booking.status === 'completed' && !booking.has_review && (
                    <button
                      onClick={() => window.location.href = `/review/${booking.id}`}
                      className="text-sm border border-green-300 text-green-600 px-3 py-1 rounded hover:bg-green-50"
                    >
                      Rate Trip
                    </button>
                  )}
                </div>
                
                <div className="text-xs text-gray-500">
                  Booked {new Date(booking.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TripHistory;
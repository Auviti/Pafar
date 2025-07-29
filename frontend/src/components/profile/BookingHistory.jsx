import React, { useState, useEffect } from 'react';
import { bookingService } from '../../services/booking';
import { paymentService } from '../../services/payment';
import BookingCancellation from './BookingCancellation';

const BookingHistory = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [showCancellation, setShowCancellation] = useState(false);

  const statusFilters = [
    { value: 'all', label: 'All Bookings' },
    { value: 'confirmed', label: 'Confirmed' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' },
    { value: 'pending', label: 'Pending' }
  ];

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const data = await bookingService.getUserBookings();
      setBookings(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredBookings = bookings.filter(booking => {
    if (filter === 'all') return true;
    return booking.status === filter;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleCancelBooking = (booking) => {
    setSelectedBooking(booking);
    setShowCancellation(true);
  };

  const handleCancellationComplete = () => {
    setShowCancellation(false);
    setSelectedBooking(null);
    fetchBookings(); // Refresh the list
  };

  const handleDownloadReceipt = async (booking) => {
    try {
      if (booking.payment_id) {
        const receipt = await paymentService.getReceipt(booking.payment_id);
        // Create a blob and download
        const blob = new Blob([receipt], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `receipt-${booking.booking_reference}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to download receipt:', error);
    }
  };

  const canCancelBooking = (booking) => {
    if (booking.status === 'cancelled' || booking.status === 'completed') {
      return false;
    }
    
    // Check if departure is more than 2 hours away
    const departureTime = new Date(booking.trip.departure_time);
    const now = new Date();
    const hoursUntilDeparture = (departureTime - now) / (1000 * 60 * 60);
    
    return hoursUntilDeparture > 2;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" role="status" aria-label="Loading"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-700">
            <strong>Error:</strong> {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">My Bookings</h2>
        
        {/* Status Filter */}
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {statusFilters.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {filteredBookings.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg mb-4">
            {filter === 'all' ? 'No bookings found' : `No ${filter} bookings found`}
          </div>
          <p className="text-gray-400">
            {filter === 'all' 
              ? 'Start by booking your first trip!' 
              : 'Try changing the filter to see other bookings.'
            }
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredBookings.map((booking) => (
            <div key={booking.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {booking.trip.route.origin_terminal.name} → {booking.trip.route.destination_terminal.name}
                  </h3>
                  <p className="text-gray-600">Booking Reference: {booking.booking_reference}</p>
                </div>
                <div className="flex space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(booking.status)}`}>
                    {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPaymentStatusColor(booking.payment_status)}`}>
                    Payment: {booking.payment_status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500">Departure</p>
                  <p className="font-medium">
                    {new Date(booking.trip.departure_time).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    {new Date(booking.trip.departure_time).toLocaleTimeString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Seats</p>
                  <p className="font-medium">
                    {booking.seat_numbers.join(', ')}
                  </p>
                  <p className="text-sm text-gray-600">
                    {booking.seat_numbers.length} seat{booking.seat_numbers.length > 1 ? 's' : ''}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Amount</p>
                  <p className="font-medium text-lg">
                    ${booking.total_amount}
                  </p>
                </div>
              </div>

              {booking.trip.bus && (
                <div className="mb-4 p-3 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-600">
                    <strong>Bus:</strong> {booking.trip.bus.license_plate} ({booking.trip.bus.model})
                  </p>
                  {booking.trip.driver && (
                    <p className="text-sm text-gray-600">
                      <strong>Driver:</strong> {booking.trip.driver.first_name} {booking.trip.driver.last_name}
                    </p>
                  )}
                </div>
              )}

              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  Booked on {new Date(booking.created_at).toLocaleDateString()}
                </div>
                <div className="flex space-x-2">
                  {booking.payment_status === 'completed' && (
                    <button
                      onClick={() => handleDownloadReceipt(booking)}
                      className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                    >
                      Download Receipt
                    </button>
                  )}
                  {canCancelBooking(booking) && (
                    <button
                      onClick={() => handleCancelBooking(booking)}
                      className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    >
                      Cancel Booking
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cancellation Modal */}
      {showCancellation && selectedBooking && (
        <BookingCancellation
          booking={selectedBooking}
          onClose={() => setShowCancellation(false)}
          onComplete={handleCancellationComplete}
        />
      )}
    </div>
  );
};

export default BookingHistory;
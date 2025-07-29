import React, { useState } from 'react';
import { bookingService } from '../../services/booking';

const BookingCancellation = ({ booking, onClose, onComplete }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reason, setReason] = useState('');

  const cancellationReasons = [
    'Change of plans',
    'Emergency',
    'Found alternative transport',
    'Trip no longer needed',
    'Other'
  ];

  const calculateRefundAmount = () => {
    const departureTime = new Date(booking.trip.departure_time);
    const now = new Date();
    const hoursUntilDeparture = (departureTime - now) / (1000 * 60 * 60);
    
    // Refund policy: 100% if >24h, 50% if >2h, 0% if <2h
    if (hoursUntilDeparture > 24) {
      return booking.total_amount;
    } else if (hoursUntilDeparture > 2) {
      return booking.total_amount * 0.5;
    } else {
      return 0;
    }
  };

  const handleCancel = async () => {
    if (!reason) {
      setError('Please select a cancellation reason');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await bookingService.cancelBooking(booking.id, { reason });
      onComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const refundAmount = calculateRefundAmount();
  const departureTime = new Date(booking.trip.departure_time);
  const now = new Date();
  const hoursUntilDeparture = (departureTime - now) / (1000 * 60 * 60);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Cancel Booking</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Booking Details */}
        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <h4 className="font-medium text-gray-900 mb-2">Booking Details</h4>
          <p className="text-sm text-gray-600">
            <strong>Route:</strong> {booking.trip.route.origin_terminal.name} → {booking.trip.route.destination_terminal.name}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Departure:</strong> {departureTime.toLocaleDateString()} at {departureTime.toLocaleTimeString()}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Seats:</strong> {booking.seat_numbers.join(', ')}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Reference:</strong> {booking.booking_reference}
          </p>
        </div>

        {/* Refund Information */}
        <div className="mb-4 p-3 bg-blue-50 rounded-md">
          <h4 className="font-medium text-blue-900 mb-2">Refund Information</h4>
          <p className="text-sm text-blue-800">
            <strong>Original Amount:</strong> ${booking.total_amount}
          </p>
          <p className="text-sm text-blue-800">
            <strong>Refund Amount:</strong> ${refundAmount.toFixed(2)}
          </p>
          {refundAmount < booking.total_amount && (
            <p className="text-xs text-blue-600 mt-1">
              {hoursUntilDeparture > 2 
                ? 'Cancellation fee applies for bookings cancelled less than 24 hours before departure'
                : 'No refund available for cancellations less than 2 hours before departure'
              }
            </p>
          )}
        </div>

        {/* Cancellation Reason */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Reason for Cancellation *
          </label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Select a reason</option>
            {cancellationReasons.map((reasonOption) => (
              <option key={reasonOption} value={reasonOption}>
                {reasonOption}
              </option>
            ))}
          </select>
        </div>

        {/* Warning */}
        <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex">
            <svg className="w-5 h-5 text-yellow-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-sm text-yellow-800 font-medium">
                This action cannot be undone
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                Once cancelled, you will not be able to use this booking. 
                {refundAmount > 0 && ' Refunds will be processed within 3-5 business days.'}
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Keep Booking
          </button>
          <button
            onClick={handleCancel}
            disabled={loading || !reason}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Cancelling...' : 'Cancel Booking'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookingCancellation;
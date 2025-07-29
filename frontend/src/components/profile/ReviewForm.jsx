import React, { useState, useEffect } from 'react';
import { reviewService } from '../../services/review';

const ReviewForm = ({ booking, existingReview, onClose, onSubmitted }) => {
  const [formData, setFormData] = useState({
    rating: 0,
    comment: '',
    driver_rating: 0,
    bus_rating: 0,
    service_rating: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (existingReview) {
      setFormData({
        rating: existingReview.rating || 0,
        comment: existingReview.comment || '',
        driver_rating: existingReview.driver_rating || 0,
        bus_rating: existingReview.bus_rating || 0,
        service_rating: existingReview.service_rating || 0
      });
    }
  }, [existingReview]);

  const handleRatingChange = (field, rating) => {
    setFormData(prev => ({
      ...prev,
      [field]: rating
    }));
  };

  const handleCommentChange = (e) => {
    setFormData(prev => ({
      ...prev,
      comment: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.rating === 0) {
      setError('Please provide an overall rating');
      return;
    }

    setLoading(true);
    setError('');

    try {
      if (existingReview) {
        await reviewService.updateReview(existingReview.id, formData);
      } else {
        await reviewService.submitReview(booking.id, formData);
      }
      onSubmitted();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderStarRating = (field, currentRating, label) => {
    return (
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label} *
        </label>
        <div className="flex space-x-1">
          {Array.from({ length: 5 }, (_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleRatingChange(field, i + 1)}
              className={`text-2xl transition-colors ${
                i < currentRating ? 'text-yellow-400' : 'text-gray-300 hover:text-yellow-200'
              }`}
            >
              ⭐
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {currentRating > 0 ? `${currentRating} out of 5 stars` : 'Click to rate'}
        </p>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {existingReview ? 'Edit Review' : 'Write Review'}
          </h3>
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

        {/* Trip Details */}
        {booking && (
          <div className="mb-6 p-4 bg-gray-50 rounded-md">
            <h4 className="font-medium text-gray-900 mb-2">Trip Details</h4>
            <p className="text-sm text-gray-600">
              <strong>Route:</strong> {booking.trip.route.origin_terminal.name} → {booking.trip.route.destination_terminal.name}
            </p>
            <p className="text-sm text-gray-600">
              <strong>Date:</strong> {new Date(booking.trip.departure_time).toLocaleDateString()}
            </p>
            <p className="text-sm text-gray-600">
              <strong>Booking:</strong> {booking.booking_reference}
            </p>
            {booking.trip.bus && (
              <p className="text-sm text-gray-600">
                <strong>Bus:</strong> {booking.trip.bus.license_plate}
              </p>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Overall Rating */}
          {renderStarRating('rating', formData.rating, 'Overall Experience')}

          {/* Detailed Ratings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderStarRating('driver_rating', formData.driver_rating, 'Driver')}
            {renderStarRating('bus_rating', formData.bus_rating, 'Bus Condition')}
          </div>

          {renderStarRating('service_rating', formData.service_rating, 'Service Quality')}

          {/* Comment */}
          <div>
            <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
              Your Review (Optional)
            </label>
            <textarea
              id="comment"
              value={formData.comment}
              onChange={handleCommentChange}
              rows={4}
              placeholder="Share your experience with other passengers..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxLength={500}
            />
            <p className="text-xs text-gray-500 mt-1">
              {formData.comment.length}/500 characters
            </p>
          </div>

          {/* Guidelines */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <h5 className="text-sm font-medium text-blue-900 mb-2">Review Guidelines</h5>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>• Be honest and constructive in your feedback</li>
              <li>• Focus on your travel experience</li>
              <li>• Avoid personal attacks or inappropriate language</li>
              <li>• Help other passengers make informed decisions</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || formData.rating === 0}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Submitting...' : (existingReview ? 'Update Review' : 'Submit Review')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ReviewForm;
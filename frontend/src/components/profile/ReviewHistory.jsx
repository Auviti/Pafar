import React, { useState, useEffect } from 'react';
import { reviewService } from '../../services/review';
import { bookingService } from '../../services/booking';
import ReviewForm from './ReviewForm';

const ReviewHistory = () => {
  const [reviews, setReviews] = useState([]);
  const [completedBookings, setCompletedBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [editingReview, setEditingReview] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [reviewsData, bookingsData] = await Promise.all([
        reviewService.getUserReviews(),
        bookingService.getUserBookings()
      ]);
      
      setReviews(reviewsData);
      
      // Filter completed bookings that don't have reviews yet
      const completedWithoutReviews = bookingsData.filter(booking => 
        booking.status === 'completed' && 
        !reviewsData.some(review => review.booking_id === booking.id)
      );
      setCompletedBookings(completedWithoutReviews);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWriteReview = (booking) => {
    setSelectedBooking(booking);
    setEditingReview(null);
    setShowReviewForm(true);
  };

  const handleEditReview = (review) => {
    setEditingReview(review);
    setSelectedBooking(null);
    setShowReviewForm(true);
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Are you sure you want to delete this review?')) {
      return;
    }

    try {
      await reviewService.deleteReview(reviewId);
      fetchData(); // Refresh the data
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReviewSubmitted = () => {
    setShowReviewForm(false);
    setSelectedBooking(null);
    setEditingReview(null);
    fetchData(); // Refresh the data
  };

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={`text-lg ${i < rating ? 'text-yellow-400' : 'text-gray-300'}`}>
        ⭐
      </span>
    ));
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
      <h2 className="text-2xl font-bold text-gray-900 mb-6">My Reviews</h2>

      {/* Pending Reviews Section */}
      {completedBookings.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Write Reviews</h3>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-blue-800 text-sm">
              You have {completedBookings.length} completed trip{completedBookings.length > 1 ? 's' : ''} waiting for your review.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {completedBookings.map((booking) => (
              <div key={booking.id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="mb-3">
                  <h4 className="font-medium text-gray-900">
                    {booking.trip.route.origin_terminal.name} → {booking.trip.route.destination_terminal.name}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {new Date(booking.trip.departure_time).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    Booking: {booking.booking_reference}
                  </p>
                </div>
                <button
                  onClick={() => handleWriteReview(booking)}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Write Review
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Submitted Reviews Section */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Reviews</h3>
        
        {reviews.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg mb-4">No reviews yet</div>
            <p className="text-gray-400">
              Complete a trip to write your first review!
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <div key={review.id} className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-1">
                      {review.booking.trip.route.origin_terminal.name} → {review.booking.trip.route.destination_terminal.name}
                    </h4>
                    <p className="text-sm text-gray-600">
                      Trip on {new Date(review.booking.trip.departure_time).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-gray-600">
                      Booking: {review.booking.booking_reference}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex">
                      {renderStars(review.rating)}
                    </div>
                    <span className="text-sm text-gray-600">
                      {review.rating}/5
                    </span>
                  </div>
                </div>

                {review.comment && (
                  <div className="mb-4">
                    <p className="text-gray-700 bg-gray-50 p-3 rounded-md">
                      "{review.comment}"
                    </p>
                  </div>
                )}

                <div className="flex justify-between items-center text-sm text-gray-500">
                  <span>
                    Reviewed on {new Date(review.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEditReview(review)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteReview(review.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {review.is_moderated && (
                  <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-yellow-800 text-sm">
                      ⚠️ This review is under moderation
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Form Modal */}
      {showReviewForm && (
        <ReviewForm
          booking={selectedBooking}
          existingReview={editingReview}
          onClose={() => setShowReviewForm(false)}
          onSubmitted={handleReviewSubmitted}
        />
      )}
    </div>
  );
};

export default ReviewHistory;
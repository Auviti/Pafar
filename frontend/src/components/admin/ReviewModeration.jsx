import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../services/admin';

const ReviewModeration = () => {
  const [filterStatus, setFilterStatus] = useState('pending');
  const [selectedReview, setSelectedReview] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [moderationReason, setModerationReason] = useState('');

  const queryClient = useQueryClient();

  const { data: reviewsData, isLoading, error } = useQuery({
    queryKey: ['admin-reviews', filterStatus],
    queryFn: () => adminService.getReviews({
      status: filterStatus !== 'all' ? filterStatus : undefined
    }),
  });

  const { data: flaggedReviews } = useQuery({
    queryKey: ['admin-flagged-reviews'],
    queryFn: () => adminService.getFlaggedReviews(),
  });

  const moderateReviewMutation = useMutation({
    mutationFn: ({ reviewId, action, reason }) => 
      adminService.moderateReview(reviewId, action, reason),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-reviews']);
      queryClient.invalidateQueries(['admin-flagged-reviews']);
      setShowReviewModal(false);
      setModerationReason('');
    },
  });

  const handleModeration = (reviewId, action) => {
    const reason = action === 'reject' ? moderationReason : '';
    if (action === 'reject' && !reason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    
    moderateReviewMutation.mutate({ reviewId, action, reason });
  };

  const ReviewModal = ({ review, onClose }) => (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Review Moderation</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="review-details">
            <div className="review-header">
              <div className="reviewer-info">
                <h4>{review.user_name}</h4>
                <p>{review.user_email}</p>
              </div>
              <div className="review-rating">
                <div className="stars">
                  {[1, 2, 3, 4, 5].map(star => (
                    <span 
                      key={star} 
                      className={star <= review.rating ? 'star filled' : 'star'}
                    >
                      ⭐
                    </span>
                  ))}
                </div>
                <span className="rating-text">{review.rating}/5</span>
              </div>
            </div>

            <div className="trip-info">
              <h5>Trip Information</h5>
              <p><strong>Route:</strong> {review.trip_route}</p>
              <p><strong>Date:</strong> {new Date(review.trip_date).toLocaleDateString()}</p>
              <p><strong>Bus:</strong> {review.bus_number}</p>
              <p><strong>Driver:</strong> {review.driver_name}</p>
            </div>

            <div className="review-content">
              <h5>Review Content</h5>
              <div className="review-text">
                {review.comment || 'No comment provided'}
              </div>
            </div>

            <div className="review-metadata">
              <p><strong>Submitted:</strong> {new Date(review.created_at).toLocaleString()}</p>
              <p><strong>Status:</strong> 
                <span className={`status-badge status-${review.status}`}>
                  {review.status}
                </span>
              </p>
              {review.flags && review.flags.length > 0 && (
                <div className="review-flags">
                  <strong>Flags:</strong>
                  {review.flags.map(flag => (
                    <span key={flag} className="flag-badge">{flag}</span>
                  ))}
                </div>
              )}
            </div>

            {review.status === 'pending' && (
              <div className="moderation-actions">
                <h5>Moderation Actions</h5>
                <div className="action-buttons">
                  <button 
                    className="btn btn-success"
                    onClick={() => handleModeration(review.id, 'approve')}
                  >
                    ✅ Approve
                  </button>
                  <button 
                    className="btn btn-danger"
                    onClick={() => handleModeration(review.id, 'reject')}
                  >
                    ❌ Reject
                  </button>
                </div>
                <div className="rejection-reason">
                  <label>Reason for rejection (if applicable):</label>
                  <textarea
                    value={moderationReason}
                    onChange={(e) => setModerationReason(e.target.value)}
                    placeholder="Enter reason for rejection..."
                    rows="3"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const ReviewCard = ({ review }) => (
    <div className={`review-card ${review.flags?.length > 0 ? 'flagged' : ''}`}>
      <div className="review-header">
        <div className="reviewer-info">
          <h4>{review.user_name}</h4>
          <div className="rating">
            {[1, 2, 3, 4, 5].map(star => (
              <span 
                key={star} 
                className={star <= review.rating ? 'star filled' : 'star'}
              >
                ⭐
              </span>
            ))}
            <span className="rating-text">({review.rating}/5)</span>
          </div>
        </div>
        <div className="review-status">
          <span className={`status-badge status-${review.status}`}>
            {review.status}
          </span>
          {review.flags?.length > 0 && (
            <span className="flag-indicator">🚩 {review.flags.length}</span>
          )}
        </div>
      </div>

      <div className="review-content">
        <div className="trip-info">
          <span>{review.trip_route}</span>
          <span>•</span>
          <span>{new Date(review.trip_date).toLocaleDateString()}</span>
        </div>
        <p className="review-text">
          {review.comment ? 
            (review.comment.length > 150 ? 
              `${review.comment.substring(0, 150)}...` : 
              review.comment
            ) : 
            'No comment provided'
          }
        </p>
      </div>

      <div className="review-footer">
        <div className="review-meta">
          <span>Submitted: {new Date(review.created_at).toLocaleDateString()}</span>
        </div>
        <div className="review-actions">
          <button 
            className="btn btn-sm btn-info"
            onClick={() => {
              setSelectedReview(review);
              setShowReviewModal(true);
            }}
          >
            View Details
          </button>
          {review.status === 'pending' && (
            <>
              <button 
                className="btn btn-sm btn-success"
                onClick={() => handleModeration(review.id, 'approve')}
              >
                Approve
              </button>
              <button 
                className="btn btn-sm btn-danger"
                onClick={() => {
                  setSelectedReview(review);
                  setShowReviewModal(true);
                }}
              >
                Reject
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return <div className="loading">Loading reviews...</div>;
  }

  if (error) {
    return <div className="error">Error loading reviews: {error.message}</div>;
  }

  return (
    <div className="review-moderation">
      <div className="page-header">
        <h2>Review Moderation</h2>
        <div className="header-stats">
          <div className="stat-item">
            <span className="stat-value">{reviewsData?.stats?.pending || 0}</span>
            <span className="stat-label">Pending Reviews</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{flaggedReviews?.length || 0}</span>
            <span className="stat-label">Flagged Reviews</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{reviewsData?.stats?.approved || 0}</span>
            <span className="stat-label">Approved Today</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="filter-tabs">
          <button 
            className={`filter-tab ${filterStatus === 'pending' ? 'active' : ''}`}
            onClick={() => setFilterStatus('pending')}
          >
            Pending ({reviewsData?.stats?.pending || 0})
          </button>
          <button 
            className={`filter-tab ${filterStatus === 'flagged' ? 'active' : ''}`}
            onClick={() => setFilterStatus('flagged')}
          >
            Flagged ({flaggedReviews?.length || 0})
          </button>
          <button 
            className={`filter-tab ${filterStatus === 'approved' ? 'active' : ''}`}
            onClick={() => setFilterStatus('approved')}
          >
            Approved
          </button>
          <button 
            className={`filter-tab ${filterStatus === 'rejected' ? 'active' : ''}`}
            onClick={() => setFilterStatus('rejected')}
          >
            Rejected
          </button>
          <button 
            className={`filter-tab ${filterStatus === 'all' ? 'active' : ''}`}
            onClick={() => setFilterStatus('all')}
          >
            All Reviews
          </button>
        </div>
      </div>

      {/* Reviews List */}
      <div className="reviews-container">
        {filterStatus === 'flagged' ? (
          <div className="reviews-list">
            {flaggedReviews?.length > 0 ? (
              flaggedReviews.map(review => (
                <ReviewCard key={review.id} review={review} />
              ))
            ) : (
              <p>No flagged reviews</p>
            )}
          </div>
        ) : (
          <div className="reviews-list">
            {reviewsData?.reviews?.length > 0 ? (
              reviewsData.reviews.map(review => (
                <ReviewCard key={review.id} review={review} />
              ))
            ) : (
              <p>No reviews found</p>
            )}
          </div>
        )}
      </div>

      {/* Review Details Modal */}
      {showReviewModal && selectedReview && (
        <ReviewModal 
          review={selectedReview} 
          onClose={() => setShowReviewModal(false)} 
        />
      )}
    </div>
  );
};

export default ReviewModeration;
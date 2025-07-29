import React from 'react';

const BookingSummary = ({ 
  trip, 
  selectedSeats = [], 
  passengerCount = 1,
  onEdit,
  onConfirm,
  loading = false 
}) => {
  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatPrice = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const calculateTotal = () => {
    if (!trip || selectedSeats.length === 0) return 0;
    return trip.fare * selectedSeats.length;
  };

  const calculateTax = () => {
    const subtotal = calculateTotal();
    return subtotal * 0.1; // 10% tax
  };

  const calculateGrandTotal = () => {
    return calculateTotal() + calculateTax();
  };

  if (!trip) {
    return (
      <div className="booking-summary empty">
        <h3>Booking Summary</h3>
        <p>Please select a trip and seats to see booking summary</p>
      </div>
    );
  }

  return (
    <div className="booking-summary">
      <div className="summary-header">
        <h3>Booking Summary</h3>
        <button className="edit-button" onClick={onEdit}>
          Edit Selection
        </button>
      </div>

      <div className="trip-summary">
        <div className="route-info">
          <div className="route-header">
            <h4>{trip.origin_terminal.name} → {trip.destination_terminal.name}</h4>
            <span className="route-cities">{trip.origin_terminal.city} to {trip.destination_terminal.city}</span>
          </div>

          <div className="journey-details">
            <div className="departure">
              <div className="label">Departure</div>
              <div className="time">{formatTime(trip.departure_time)}</div>
              <div className="date">{formatDate(trip.departure_time)}</div>
            </div>

            <div className="duration">
              <div className="label">Duration</div>
              <div className="time">{formatDuration(trip.estimated_duration)}</div>
            </div>

            <div className="arrival">
              <div className="label">Arrival</div>
              <div className="time">{formatTime(trip.arrival_time)}</div>
              <div className="date">{formatDate(trip.arrival_time)}</div>
            </div>
          </div>
        </div>

        <div className="bus-info">
          <h5>Bus Information</h5>
          <div className="bus-details">
            <span className="bus-model">{trip.bus.model}</span>
            <span className="bus-plate">({trip.bus.license_plate})</span>
          </div>
          
          {trip.bus.amenities && trip.bus.amenities.length > 0 && (
            <div className="amenities">
              <span className="amenities-label">Amenities:</span>
              {trip.bus.amenities.map((amenity, index) => (
                <span key={index} className="amenity">{amenity}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="seat-summary">
        <h5>Selected Seats</h5>
        {selectedSeats.length > 0 ? (
          <div className="seats-list">
            {selectedSeats.map(seatNumber => (
              <div key={seatNumber} className="seat-item">
                <span className="seat-number">Seat {seatNumber}</span>
                <span className="seat-price">{formatPrice(trip.fare)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-seats">No seats selected</p>
        )}
      </div>

      <div className="price-breakdown">
        <h5>Price Breakdown</h5>
        
        <div className="price-item">
          <span>Subtotal ({selectedSeats.length} seat{selectedSeats.length !== 1 ? 's' : ''})</span>
          <span>{formatPrice(calculateTotal())}</span>
        </div>

        <div className="price-item">
          <span>Tax (10%)</span>
          <span>{formatPrice(calculateTax())}</span>
        </div>

        <div className="price-item total">
          <span>Total Amount</span>
          <span>{formatPrice(calculateGrandTotal())}</span>
        </div>
      </div>

      <div className="booking-actions">
        <button
          className="confirm-button"
          onClick={() => onConfirm({
            trip,
            selectedSeats,
            totalAmount: calculateGrandTotal(),
            subtotal: calculateTotal(),
            tax: calculateTax()
          })}
          disabled={loading || selectedSeats.length === 0}
        >
          {loading ? 'Processing...' : 'Proceed to Payment'}
        </button>
      </div>

      <div className="booking-terms">
        <p className="terms-text">
          By proceeding, you agree to our{' '}
          <a href="/terms" target="_blank" rel="noopener noreferrer">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="/privacy" target="_blank" rel="noopener noreferrer">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
};

export default BookingSummary;
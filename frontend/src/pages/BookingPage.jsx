import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TripSearchForm from '../components/booking/TripSearchForm';
import TripResults from '../components/booking/TripResults';
import SeatMap from '../components/booking/SeatMap';
import BookingSummary from '../components/booking/BookingSummary';
import PaymentForm from '../components/booking/PaymentForm';
import { bookingService } from '../services/booking';

const BOOKING_STEPS = {
  SEARCH: 'search',
  RESULTS: 'results',
  SEATS: 'seats',
  SUMMARY: 'summary',
  PAYMENT: 'payment',
  SUCCESS: 'success',
  ERROR: 'error'
};

const BookingPage = () => {
  const navigate = useNavigate();
  
  // State management
  const [currentStep, setCurrentStep] = useState(BOOKING_STEPS.SEARCH);
  const [searchParams, setSearchParams] = useState(null);
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [bookingData, setBookingData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Search for trips
  const handleTripSearch = async (params) => {
    try {
      setLoading(true);
      setError(null);
      setSearchParams(params);
      
      const response = await bookingService.searchTrips(params);
      setTrips(response.trips || []);
      setCurrentStep(BOOKING_STEPS.RESULTS);
    } catch (err) {
      setError(err.message);
      setTrips([]);
    } finally {
      setLoading(false);
    }
  };

  // Select a trip and move to seat selection
  const handleTripSelect = async (trip) => {
    try {
      setLoading(true);
      setError(null);
      
      // Get detailed trip info with seat availability
      const tripDetails = await bookingService.getTripDetails(trip.id);
      setSelectedTrip(tripDetails);
      setSelectedSeats([]);
      setCurrentStep(BOOKING_STEPS.SEATS);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle seat selection
  const handleSeatSelect = (seats) => {
    setSelectedSeats(seats);
  };

  // Move to booking summary
  const handleProceedToSummary = () => {
    if (selectedSeats.length === 0) {
      setError('Please select at least one seat');
      return;
    }
    setCurrentStep(BOOKING_STEPS.SUMMARY);
  };

  // Proceed to payment
  const handleProceedToPayment = async (summaryData) => {
    try {
      setLoading(true);
      setError(null);

      // Create booking
      const bookingResponse = await bookingService.createBooking({
        trip_id: selectedTrip.id,
        seat_numbers: selectedSeats,
        total_amount: summaryData.totalAmount
      });

      setBookingData({
        ...summaryData,
        bookingId: bookingResponse.booking.id,
        bookingReference: bookingResponse.booking.booking_reference
      });

      setCurrentStep(BOOKING_STEPS.PAYMENT);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle successful payment
  const handlePaymentSuccess = (paymentData) => {
    setBookingData(prev => ({
      ...prev,
      paymentIntent: paymentData.paymentIntent
    }));
    setCurrentStep(BOOKING_STEPS.SUCCESS);
  };

  // Handle payment error
  const handlePaymentError = (error) => {
    setError(error.message || 'Payment failed');
    setCurrentStep(BOOKING_STEPS.ERROR);
  };

  // Navigation helpers
  const goBack = () => {
    switch (currentStep) {
      case BOOKING_STEPS.RESULTS:
        setCurrentStep(BOOKING_STEPS.SEARCH);
        break;
      case BOOKING_STEPS.SEATS:
        setCurrentStep(BOOKING_STEPS.RESULTS);
        break;
      case BOOKING_STEPS.SUMMARY:
        setCurrentStep(BOOKING_STEPS.SEATS);
        break;
      case BOOKING_STEPS.PAYMENT:
        setCurrentStep(BOOKING_STEPS.SUMMARY);
        break;
      default:
        break;
    }
  };

  const startNewBooking = () => {
    setCurrentStep(BOOKING_STEPS.SEARCH);
    setSearchParams(null);
    setTrips([]);
    setSelectedTrip(null);
    setSelectedSeats([]);
    setBookingData(null);
    setError(null);
  };

  const formatPrice = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <div className="booking-page">
      {/* Progress Indicator */}
      <div className="booking-progress">
        <div className={`step ${currentStep === BOOKING_STEPS.SEARCH ? 'active' : ''} ${['results', 'seats', 'summary', 'payment', 'success'].includes(currentStep) ? 'completed' : ''}`}>
          <span className="step-number">1</span>
          <span className="step-label">Search</span>
        </div>
        <div className={`step ${currentStep === BOOKING_STEPS.RESULTS ? 'active' : ''} ${['seats', 'summary', 'payment', 'success'].includes(currentStep) ? 'completed' : ''}`}>
          <span className="step-number">2</span>
          <span className="step-label">Select Trip</span>
        </div>
        <div className={`step ${currentStep === BOOKING_STEPS.SEATS ? 'active' : ''} ${['summary', 'payment', 'success'].includes(currentStep) ? 'completed' : ''}`}>
          <span className="step-number">3</span>
          <span className="step-label">Choose Seats</span>
        </div>
        <div className={`step ${currentStep === BOOKING_STEPS.SUMMARY ? 'active' : ''} ${['payment', 'success'].includes(currentStep) ? 'completed' : ''}`}>
          <span className="step-number">4</span>
          <span className="step-label">Review</span>
        </div>
        <div className={`step ${currentStep === BOOKING_STEPS.PAYMENT ? 'active' : ''} ${currentStep === BOOKING_STEPS.SUCCESS ? 'completed' : ''}`}>
          <span className="step-number">5</span>
          <span className="step-label">Payment</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
          <button onClick={() => setError(null)} className="close-error">×</button>
        </div>
      )}

      {/* Back Button */}
      {currentStep !== BOOKING_STEPS.SEARCH && currentStep !== BOOKING_STEPS.SUCCESS && currentStep !== BOOKING_STEPS.ERROR && (
        <button onClick={goBack} className="back-button">
          ← Back
        </button>
      )}

      {/* Step Content */}
      <div className="booking-content">
        {currentStep === BOOKING_STEPS.SEARCH && (
          <TripSearchForm 
            onSearch={handleTripSearch}
            loading={loading}
          />
        )}

        {currentStep === BOOKING_STEPS.RESULTS && (
          <TripResults 
            trips={trips}
            loading={loading}
            onSelectTrip={handleTripSelect}
          />
        )}

        {currentStep === BOOKING_STEPS.SEATS && (
          <div className="seats-step">
            <SeatMap 
              trip={selectedTrip}
              selectedSeats={selectedSeats}
              onSeatSelect={handleSeatSelect}
              maxSeats={searchParams?.passengers || 1}
              loading={loading}
            />
            <div className="seats-actions">
              <button 
                onClick={handleProceedToSummary}
                className="proceed-button"
                disabled={selectedSeats.length === 0}
              >
                Continue to Summary
              </button>
            </div>
          </div>
        )}

        {currentStep === BOOKING_STEPS.SUMMARY && (
          <BookingSummary 
            trip={selectedTrip}
            selectedSeats={selectedSeats}
            passengerCount={searchParams?.passengers || 1}
            onEdit={() => setCurrentStep(BOOKING_STEPS.SEATS)}
            onConfirm={handleProceedToPayment}
            loading={loading}
          />
        )}

        {currentStep === BOOKING_STEPS.PAYMENT && (
          <PaymentForm 
            bookingData={bookingData}
            onPaymentSuccess={handlePaymentSuccess}
            onPaymentError={handlePaymentError}
            loading={loading}
          />
        )}

        {currentStep === BOOKING_STEPS.SUCCESS && (
          <div className="booking-success">
            <div className="success-icon">✅</div>
            <h2>Booking Confirmed!</h2>
            <div className="booking-details">
              <p><strong>Booking Reference:</strong> {bookingData?.bookingReference}</p>
              <p><strong>Trip:</strong> {selectedTrip?.origin_terminal.name} → {selectedTrip?.destination_terminal.name}</p>
              <p><strong>Departure:</strong> {formatTime(selectedTrip?.departure_time)}</p>
              <p><strong>Seats:</strong> {selectedSeats.join(', ')}</p>
              <p><strong>Total Paid:</strong> {formatPrice(bookingData?.totalAmount)}</p>
            </div>
            <div className="success-actions">
              <button onClick={() => navigate('/bookings')} className="view-bookings-button">
                View My Bookings
              </button>
              <button onClick={startNewBooking} className="new-booking-button">
                Book Another Trip
              </button>
            </div>
          </div>
        )}

        {currentStep === BOOKING_STEPS.ERROR && (
          <div className="booking-error">
            <div className="error-icon">❌</div>
            <h2>Booking Failed</h2>
            <p>{error}</p>
            <div className="error-actions">
              <button onClick={() => setCurrentStep(BOOKING_STEPS.PAYMENT)} className="retry-button">
                Try Again
              </button>
              <button onClick={startNewBooking} className="new-booking-button">
                Start New Booking
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BookingPage;
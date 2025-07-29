import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import { paymentService } from '../../services/payment';

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      '::placeholder': {
        color: '#aab7c4',
      },
    },
    invalid: {
      color: '#9e2146',
    },
  },
};

const PaymentFormContent = ({ 
  bookingData, 
  onPaymentSuccess, 
  onPaymentError,
  loading: externalLoading = false 
}) => {
  const stripe = useStripe();
  const elements = useElements();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [paymentIntent, setPaymentIntent] = useState(null);
  const [saveCard, setSaveCard] = useState(false);
  const [savedCards, setSavedCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState('');

  useEffect(() => {
    if (bookingData) {
      createPaymentIntent();
      loadSavedCards();
    }
  }, [bookingData]);

  const createPaymentIntent = async () => {
    try {
      setLoading(true);
      const response = await paymentService.createPaymentIntent(
        bookingData.bookingId,
        bookingData.totalAmount
      );
      setPaymentIntent(response.payment_intent);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSavedCards = async () => {
    try {
      const response = await paymentService.getSavedPaymentMethods();
      setSavedCards(response.payment_methods || []);
    } catch (err) {
      console.error('Failed to load saved cards:', err);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!stripe || !elements || !paymentIntent) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let result;

      if (selectedCard) {
        // Use saved payment method
        result = await stripe.confirmCardPayment(paymentIntent.client_secret, {
          payment_method: selectedCard
        });
      } else {
        // Use new card
        const cardElement = elements.getElement(CardElement);
        
        result = await stripe.confirmCardPayment(paymentIntent.client_secret, {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: bookingData.passengerName || 'Customer',
            },
          }
        });

        // Save card if requested
        if (saveCard && result.paymentIntent.status === 'succeeded') {
          try {
            await paymentService.savePaymentMethod(result.paymentIntent.payment_method);
          } catch (saveError) {
            console.error('Failed to save payment method:', saveError);
          }
        }
      }

      if (result.error) {
        setError(result.error.message);
        onPaymentError(result.error);
      } else {
        // Payment succeeded
        onPaymentSuccess({
          paymentIntent: result.paymentIntent,
          bookingData
        });
      }
    } catch (err) {
      setError(err.message);
      onPaymentError(err);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const isFormLoading = loading || externalLoading;

  return (
    <div className="payment-form">
      <div className="payment-header">
        <h3>Payment Details</h3>
        <div className="amount-display">
          <span className="amount">{formatPrice(bookingData?.totalAmount || 0)}</span>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="payment-form-content">
        {/* Saved Cards Section */}
        {savedCards.length > 0 && (
          <div className="saved-cards-section">
            <h4>Saved Payment Methods</h4>
            <div className="saved-cards">
              <label className="card-option">
                <input
                  type="radio"
                  name="paymentMethod"
                  value=""
                  checked={selectedCard === ''}
                  onChange={(e) => setSelectedCard(e.target.value)}
                />
                <span>Use new card</span>
              </label>
              
              {savedCards.map((card) => (
                <label key={card.id} className="card-option">
                  <input
                    type="radio"
                    name="paymentMethod"
                    value={card.id}
                    checked={selectedCard === card.id}
                    onChange={(e) => setSelectedCard(e.target.value)}
                  />
                  <span>
                    **** **** **** {card.last4} ({card.brand.toUpperCase()})
                    <span className="expiry">Exp: {card.exp_month}/{card.exp_year}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* New Card Section */}
        {selectedCard === '' && (
          <div className="new-card-section">
            <h4>Card Information</h4>
            
            <div className="card-input">
              <label htmlFor="card-element">
                Credit or Debit Card
              </label>
              <div className="card-element-container">
                <CardElement
                  id="card-element"
                  options={CARD_ELEMENT_OPTIONS}
                />
              </div>
            </div>

            <div className="save-card-option">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={saveCard}
                  onChange={(e) => setSaveCard(e.target.checked)}
                />
                <span>Save this card for future purchases</span>
              </label>
            </div>
          </div>
        )}

        {/* Security Notice */}
        <div className="security-notice">
          <div className="security-icons">
            <span>🔒</span>
            <span>💳</span>
          </div>
          <p>Your payment information is encrypted and secure. We use Stripe for payment processing.</p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="pay-button"
          disabled={!stripe || isFormLoading || !paymentIntent}
        >
          {isFormLoading ? (
            <>
              <span className="spinner"></span>
              Processing Payment...
            </>
          ) : (
            <>
              Pay {formatPrice(bookingData?.totalAmount || 0)}
            </>
          )}
        </button>
      </form>

      {/* Accepted Cards */}
      <div className="accepted-cards">
        <span>We accept:</span>
        <div className="card-brands">
          <span className="card-brand">Visa</span>
          <span className="card-brand">Mastercard</span>
          <span className="card-brand">American Express</span>
          <span className="card-brand">Discover</span>
        </div>
      </div>
    </div>
  );
};

const PaymentForm = (props) => {
  return (
    <Elements stripe={stripePromise}>
      <PaymentFormContent {...props} />
    </Elements>
  );
};

export default PaymentForm;
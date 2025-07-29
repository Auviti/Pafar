import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import PaymentForm from '../PaymentForm';
import { paymentService } from '../../../services/payment';

// Mock Stripe
vi.mock('@stripe/stripe-js', () => ({
  loadStripe: vi.fn(() => Promise.resolve({
    confirmCardPayment: vi.fn()
  }))
}));

vi.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }) => children,
  CardElement: () => <div data-testid="card-element">Card Element</div>,
  useStripe: () => ({
    confirmCardPayment: vi.fn()
  }),
  useElements: () => ({
    getElement: vi.fn(() => ({}))
  })
}));

// Mock payment service
vi.mock('../../../services/payment', () => ({
  paymentService: {
    createPaymentIntent: vi.fn(),
    getSavedPaymentMethods: vi.fn()
  }
}));

const mockBookingData = {
  bookingId: 'booking-123',
  totalAmount: 110.00,
  passengerName: 'John Doe'
};

describe('PaymentForm', () => {
  const mockOnPaymentSuccess = vi.fn();
  const mockOnPaymentError = vi.fn();
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    paymentService.createPaymentIntent.mockResolvedValue({
      payment_intent: {
        client_secret: 'pi_test_client_secret'
      }
    });
    paymentService.getSavedPaymentMethods.mockResolvedValue({
      payment_methods: []
    });
  });

  it('renders payment form with amount', async () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(screen.getByText('Payment Details')).toBeInTheDocument();
    expect(screen.getByText('$110.00')).toBeInTheDocument();
  });

  it('shows card input for new payment', async () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(screen.getByText('Card Information')).toBeInTheDocument();
    expect(screen.getByTestId('card-element')).toBeInTheDocument();
  });

  it('shows security notice', () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(screen.getByText(/Your payment information is encrypted and secure/)).toBeInTheDocument();
  });

  it('shows accepted card brands', () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(screen.getByText('We accept:')).toBeInTheDocument();
    expect(screen.getByText('Visa')).toBeInTheDocument();
    expect(screen.getByText('Mastercard')).toBeInTheDocument();
    expect(screen.getByText('American Express')).toBeInTheDocument();
    expect(screen.getByText('Discover')).toBeInTheDocument();
  });

  it('creates payment intent on mount', async () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(paymentService.createPaymentIntent).toHaveBeenCalledWith(
      'booking-123',
      110.00
    );
  });

  it('loads saved payment methods on mount', async () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(paymentService.getSavedPaymentMethods).toHaveBeenCalled();
  });

  it('shows save card option', () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
      />
    );

    expect(screen.getByText('Save this card for future purchases')).toBeInTheDocument();
  });

  it('disables pay button when loading', () => {
    render(
      <PaymentForm 
        bookingData={mockBookingData}
        onPaymentSuccess={mockOnPaymentSuccess}
        onPaymentError={mockOnPaymentError}
        loading={true}
      />
    );

    const payButton = screen.getByRole('button', { name: /processing payment/i });
    expect(payButton).toBeDisabled();
  });
});